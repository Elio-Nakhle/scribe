import datetime
import os
import pathlib

import typer

from scribe.pipeline import run_pipeline
from scribe.audio_utils import record_audio

MEETING_NAME = f"meeting-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
MEETING_DIR = pathlib.Path(__file__).parent.parent.parent / "records" / MEETING_NAME
MEETING_RECORD = str(MEETING_DIR / MEETING_NAME) + ".wav"
COMPRESSED_MEETING_RECORD = str(MEETING_DIR / MEETING_NAME) + ".mp3"

app = typer.Typer()


def record():
    os.makedirs(MEETING_DIR, exist_ok=True)
    record_audio(MEETING_RECORD)


def convert():
    os.system(f"ffmpeg -i {MEETING_RECORD} -acodec mp3 {COMPRESSED_MEETING_RECORD}")
    os.remove(MEETING_RECORD)


def cleanup():
    """
    Clean up the meeting directory and its contents.
    This function is called when the script is interrupted or exits.
    """
    if MEETING_DIR.exists():
        for file in MEETING_DIR.iterdir():
            file.unlink()
        MEETING_DIR.rmdir()


@app.command()
def meet(
    diarization: bool = typer.Option(
        False,
        "--diarization",
        help="Enable speaker diarization (use HF_TOKEN for pyannote, or Resemblyzer when unset).",
    ),
    sentiment: bool = typer.Option(
        False,
        "--sentiment",
        help="Enable per-segment sentiment analysis.",
    ),
):
    """
    Record and transcribe a meeting. Optionally enable diarization and/or sentiment with flags.
    Writes MP3 and timestamped TXT to records/meeting-YYYY-MM-DD_HH-MM-SS/.
    """
    try:
        record()
        run_pipeline(
            MEETING_RECORD,
            str(MEETING_DIR / MEETING_NAME),
            diarization=diarization,
            sentiment=sentiment,
        )
        convert()
    except Exception:
        cleanup()
        raise


if __name__ == "__main__":
    app()
