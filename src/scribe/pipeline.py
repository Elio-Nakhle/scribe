"""
Meeting pipeline: transcribe → optional diarization → optional sentiment → write TXT.
"""

import time
from typing import List, Optional

from scribe.transcribe import get_segments


def _format_line(
    start: float,
    end: float,
    text: str,
    speaker: Optional[str] = None,
    sentiment_label: Optional[str] = None,
) -> str:
    """Build one transcript line. Backwards compatible when speaker and sentiment are None."""
    prefix = "[%.2fs -> %.2fs]" % (start, end)
    if speaker is not None:
        prefix += " %s:" % speaker
    if sentiment_label is not None:
        prefix += " (%s):" % sentiment_label
    prefix += " "
    return prefix + text


def run_pipeline(
    audio_path: str,
    output_base_path: str,
    *,
    diarization: bool = False,
    sentiment: bool = False,
) -> None:
    """
    Run full pipeline: transcribe, optionally diarize and add sentiment, write TXT.
    output_base_path: path without extension (e.g. records/meeting-xxx/meeting-xxx).
    """
    start_time = time.time()

    # 1. Transcribe
    segments, info = get_segments(audio_path)
    print(
        "Detected language '%s' with probability %f"
        % (info.language, info.language_probability)
    )

    if not segments:
        with open(output_base_path + ".txt", "w") as f:
            pass
        print("No segments transcribed.")
        return

    # 2. Optional diarization + align
    speakers: Optional[List[str]] = None
    if diarization:
        from scribe.diarize import run_diarization, align_speakers_to_segments

        diar_segments = run_diarization(audio_path, whisper_segments=segments)
        speakers = align_speakers_to_segments(segments, diar_segments)

    # 3. Optional sentiment
    sentiment_labels: Optional[List[str]] = None
    if sentiment:
        from scribe.sentiment import run_sentiment

        texts = [text for _, _, text in segments]
        results = run_sentiment(texts)
        sentiment_labels = [label for label, _ in results]

    # 4. Build lines and write
    lines = []
    for i, (s, e, text) in enumerate(segments):
        sp = speakers[i] if speakers else None
        sent = sentiment_labels[i] if sentiment_labels else None
        line = _format_line(s, e, text, speaker=sp, sentiment_label=sent)
        print(line)
        lines.append(line)

    txt_path = output_base_path + ".txt"
    with open(txt_path, "w") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"Pipeline took: {time.time() - start_time:.1f} seconds")
