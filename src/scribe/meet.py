import os
import datetime
import pathlib

import typer

from scribe.transcribe import transcribe

MEETING_NAME = f"meeting-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
MEETING_DIR = pathlib.Path(__file__).parent.parent.parent / "records" / MEETING_NAME
MEETING_RECORD = MEETING_DIR / f"{MEETING_NAME}.wav"

app = typer.Typer()


def record():
    os.system(f"mkdir -p {MEETING_DIR}")
    os.system(f"arecord {MEETING_RECORD}")


def convert():
    os.system(
        f"ffmpeg -i {MEETING_RECORD} -acodec mp3 {MEETING_RECORD.with_suffix('.mp3')}"
    )


@app.command()
def meet():
    """
    Main function to handle the meeting workflow.
    It orchestrates the recording, converting, and transcribing of the meeting audio.
    """
    record()
    convert()
    transcribe(MEETING_RECORD, MEETING_DIR / MEETING_NAME)


if __name__ == "__main__":
    app()
