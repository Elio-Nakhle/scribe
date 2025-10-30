# scribe

Utility to record and transcribe meetings. Uses Sox for cross-platform audio recording.

## Installation

```bash
# Install Python dependencies
pdm install

# Install Sox (required for audio recording)
# macOS:
brew install sox

# Linux (Ubuntu/Debian):
sudo apt install sox

# Linux (RedHat/CentOS):
sudo yum install sox
```

## Usage

```bash
# Record and transcribe a meeting
pdm run meet

# Record audio only
pdm run record my-recording                    # With timestamp
pdm run record my-recording --no-timestamp     # Without timestamp
```

## Output

Creates a folder in `records/` with:

- Audio file (WAV → MP3)
- Transcription with timestamps (TXT)
