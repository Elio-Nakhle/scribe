"""
Speaker diarization: pyannote-audio (requires HF token) or Resemblyzer (free, no token).

- With HF_TOKEN: uses pyannote/speaker-diarization-3.1 (accept model conditions on Hugging Face).
- Without HF_TOKEN: uses Resemblyzer (embed + cluster), no account needed.
"""

import os
from typing import List, Tuple

# Diarization segment: (start_sec, end_sec, speaker_id)
DiarizationSegment = Tuple[float, float, str]

# Resemblyzer uses 16 kHz (matches our recording)
_RESEMBLYZER_SAMPLE_RATE = 16000

_MIN_SEGMENT_DURATION_FOR_EMBED = 0.4  # seconds; shorter segments inherit from neighbour


def _has_hf_token() -> bool:
    return bool(
        os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    )


def _get_hf_token() -> str:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        raise RuntimeError(
            "Speaker diarization with pyannote requires a Hugging Face token. "
            "Set HF_TOKEN (or HUGGING_FACE_HUB_TOKEN), accept the model conditions at "
            "https://huggingface.co/pyannote/speaker-diarization-3.1 and "
            "https://huggingface.co/pyannote/segmentation-3.0, then create a token at "
            "https://hf.co/settings/tokens. Alternatively, run without HF_TOKEN to use "
            "the free Resemblyzer-based diarization (no account needed)."
        )
    return token


def _run_diarization_resemblyzer(
    audio_path: str,
    whisper_segments: List[Tuple[float, float, str]],
) -> List[DiarizationSegment]:
    """
    Diarize using Resemblyzer (no HF token): embed each segment, cluster, assign Speaker_0/1/...
    Returns one (start, end, speaker_id) per whisper segment for alignment.
    """
    from resemblyzer import preprocess_wav, VoiceEncoder
    from sklearn.cluster import AgglomerativeClustering
    import numpy as np

    wav = preprocess_wav(audio_path)
    encoder = VoiceEncoder(device="cpu")

    embeddings_list: List[Tuple[int, float, float, float, str, np.ndarray | None]] = []
    for i, (start, end, text) in enumerate(whisper_segments):
        duration = end - start
        start_samp = int(start * _RESEMBLYZER_SAMPLE_RATE)
        end_samp = int(end * _RESEMBLYZER_SAMPLE_RATE)
        end_samp = min(end_samp, len(wav))
        if start_samp >= end_samp:
            embeddings_list.append((i, start, end, duration, text, None))
            continue
        chunk = wav[start_samp:end_samp]
        if duration < _MIN_SEGMENT_DURATION_FOR_EMBED:
            embeddings_list.append((i, start, end, duration, text, None))
            continue
        try:
            emb = encoder.embed_utterance(chunk)
            embeddings_list.append((i, start, end, duration, text, emb))
        except Exception:
            embeddings_list.append((i, start, end, duration, text, None))

    # Build matrix of embeddings (only rows with valid embed)
    valid_indices = [j for j, t in enumerate(embeddings_list) if t[5] is not None]
    if not valid_indices:
        return [(s, e, "Speaker_0") for (_, s, e, _, _, _) in embeddings_list]

    X = np.stack([embeddings_list[j][5] for j in valid_indices])
    n = len(valid_indices)
    n_clusters = min(max(2, n // 3), 10)
    clustering = AgglomerativeClustering(n_clusters=n_clusters, metric="cosine", linkage="average")
    labels = clustering.fit_predict(X)

    # Map valid index back to segment index and assign labels
    idx_to_label = {valid_indices[j]: labels[j] for j in range(len(valid_indices))}
    segment_labels: List[int] = []
    for j in range(len(embeddings_list)):
        if embeddings_list[j][5] is not None:
            segment_labels.append(idx_to_label[j])
        else:
            # Short or failed: use previous segment's label or 0
            prev_label = segment_labels[-1] if segment_labels else 0
            segment_labels.append(prev_label)

    return [
        (start, end, f"Speaker_{segment_labels[i]}")
        for i, (_, start, end, _, _, _) in enumerate(embeddings_list)
    ]


def run_diarization(
    audio_path: str,
    hf_token: str | None = None,
    whisper_segments: List[Tuple[float, float, str]] | None = None,
) -> List[DiarizationSegment]:
    """
    Run speaker diarization on an audio file.
    - If hf_token or HF_TOKEN is set: use pyannote (best quality).
    - Else if whisper_segments is provided: use Resemblyzer (no token, free).
    - Else: raise (need token or segments for free backend).
    Returns a list of (start, end, speaker_id) in seconds.
    """
    if hf_token or _has_hf_token():
        from pyannote.audio import Pipeline

        token = hf_token or _get_hf_token()
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token,
        )
        diarization = pipeline(audio_path)

        segments: List[DiarizationSegment] = []
        for turn, _, speaker in diarization.itertracks(label=True):
            segments.append((turn.start, turn.end, speaker))

        return segments

    if whisper_segments is not None:
        try:
            return _run_diarization_resemblyzer(audio_path, whisper_segments)
        except ImportError as e:
            raise RuntimeError(
                "Resemblyzer-based diarization (no HF token) requires: pip install Resemblyzer scikit-learn. "
                "Error: %s" % e
            ) from e

    raise RuntimeError(
        "Speaker diarization needs either: (1) HF_TOKEN set for pyannote, or "
        "(2) Resemblyzer installed and segments provided (handled by the pipeline)."
    )


def align_speakers_to_segments(
    whisper_segments: List[Tuple[float, float, str]],
    diarization_segments: List[DiarizationSegment],
) -> List[str]:
    """
    Assign a speaker to each Whisper segment by maximum time overlap with
    diarization segments.
    whisper_segments: list of (start, end, text)
    diarization_segments: list of (start, end, speaker_id)
    Returns: list of speaker_id, one per whisper segment.
    """
    if not diarization_segments:
        return ["Speaker_0"] * len(whisper_segments)

    result = []
    for seg_start, seg_end, _ in whisper_segments:
        best_speaker = None
        best_overlap = -1.0
        for d_start, d_end, speaker in diarization_segments:
            overlap_start = max(seg_start, d_start)
            overlap_end = min(seg_end, d_end)
            if overlap_end > overlap_start:
                overlap = overlap_end - overlap_start
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = speaker
        result.append(best_speaker if best_speaker else "Speaker_0")
    return result
