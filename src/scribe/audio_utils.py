"""Simple audio recording with Sox support for macOS and Linux."""

import platform
import subprocess

# Check if sox is available
try:
    import sox

    SOX_AVAILABLE = True
except ImportError:
    SOX_AVAILABLE = False


def record_audio(output_file: str) -> str:
    """Record audio using Sox for cross-platform compatibility."""
    system = platform.system()

    if system == "Darwin":
        # macOS: use CoreAudio
        cmd = [
            "sox",
            "-t",
            "coreaudio",
            "default",
            "-r",
            "16000",
            "-c",
            "1",
            "-b",
            "16",
            output_file,
        ]
    elif system == "Linux":
        # Linux: use ALSA
        cmd = [
            "sox",
            "-t",
            "alsa",
            "default",
            "-r",
            "16000",
            "-c",
            "1",
            "-b",
            "16",
            output_file,
        ]
    else:
        # Other systems: try pulseaudio or default
        cmd = [
            "sox",
            "-d",  # default audio device
            "-r",
            "16000",
            "-c",
            "1",
            "-b",
            "16",
            output_file,
        ]

    print(f"Recording with Sox on {system} (press Ctrl+C to stop)...")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print(f"\nRecording saved: {output_file}")
    except FileNotFoundError:
        print("Error: Sox not found. Please install sox:")
        print("  macOS: brew install sox")
        print(
            "  Linux: apt install sox (Ubuntu/Debian) or yum install sox (RedHat/CentOS)"
        )
        raise
    except subprocess.CalledProcessError as e:
        print(f"Sox recording failed: {e}")
        print("Make sure your audio device is available and sox is properly installed.")
        raise

    return output_file


# CLI interface when run as module
if __name__ == "__main__":
    import datetime
    import typer

    app = typer.Typer()

    @app.command()
    def record(
        name: str = typer.Argument(..., help="Name for the recording"),
        timestamp: bool = typer.Option(
            True, "--timestamp/--no-timestamp", help="Add timestamp to filename"
        ),
    ):
        """Record audio using Sox."""
        if timestamp:
            time_suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{name}-{time_suffix}.wav"
        else:
            filename = f"{name}.wav"

        print(f"Recording: {filename}")
        record_audio(filename)

    app()
