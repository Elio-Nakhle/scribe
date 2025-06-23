import os
import datetime
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


@app.command()
def meet():
    """
    Main function to handle the meeting workflow.
    It orchestrates the recording, converting, and transcribing of the meeting audio.
    """
    record()
    convert()
    transcribe(COMPRESSED_MEETING_RECORD, str(MEETING_DIR / MEETING_NAME))


if __name__ == "__main__":
    app()
