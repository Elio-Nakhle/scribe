import time
from typing import List, Tuple, Any

from faster_whisper import WhisperModel

# (start_sec, end_sec, text) per segment
WhisperSegment = Tuple[float, float, str]


def get_segments(audio_file: str) -> Tuple[List[WhisperSegment], Any]:
    """
    Run Whisper transcription and return segment list and info.
    segments: list of (start, end, text) in seconds.
    """
    model = WhisperModel("turbo", device="cpu")
    segment_iter, info = model.transcribe(audio_file, beam_size=5, vad_filter=True)
    segments = [(s.start, s.end, s.text) for s in segment_iter]
    return segments, info


def transcribe(audio_file: str, meeting_name: str) -> None:
    """
    Transcribe audio and write timestamped TXT (legacy: no diarization/sentiment).
    For diarization and sentiment, use pipeline.run_pipeline instead.
    """
    start_time = time.time()
    segments, info = get_segments(audio_file)

    print(
        "Detected language '%s' with probability %f"
        % (info.language, info.language_probability)
    )

    lines = []
    for start, end, text in segments:
        line = "[%.2fs -> %.2fs] %s" % (start, end, text)
        print(line)
        lines.append(line)

    with open(meeting_name + ".txt", "w") as file:
        for line in lines:
            file.write(f"{line}\n")

    print(f"Transcription took: {time.time() - start_time} seconds")
