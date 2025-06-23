import datetime
import os
import pathlib

import typer

from scribe.transcribe import transcribe

MEETING_NAME = f"meeting-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
MEETING_DIR = pathlib.Path(__file__).parent.parent.parent / "records" / MEETING_NAME
MEETING_RECORD = str(MEETING_DIR / MEETING_NAME) + ".wav"
COMPRESSED_MEETING_RECORD = str(MEETING_DIR / MEETING_NAME) + ".mp3"

app = typer.Typer()


def record():
    os.system(f"mkdir -p {MEETING_DIR}")
    os.system(f"arecord {MEETING_RECORD}")


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
def meet():
    """
    Main function to handle the meeting workflow.
    It orchestrates the recording, converting, and transcribing of the meeting audio.
    """
    try:
        record()
        transcribe(MEETING_RECORD, str(MEETING_DIR / MEETING_NAME))
        convert()
    except Exception:
        cleanup()


if __name__ == "__main__":
    app()
