# scribe

Utility to record and transcribe meetings. Uses Sox for cross-platform audio recording. Supports optional **speaker diarization** (who spoke when) and **per-segment sentiment analysis**.

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

### Speaker diarization (optional)

Diarization is **off by default**; pass `--diarization` to enable it. You can use it in two ways:

**Option 1: No account (free)**  
If you do **not** set `HF_TOKEN`, scribe uses **Resemblyzer** to diarize: it embeds each transcript segment and clusters by voice. No Hugging Face account or token is required. Install the extra deps (included in `pdm install`): `Resemblyzer`, `scikit-learn`.

**Option 2: Pyannote (best quality)**  
For higher-quality diarization, use [Hugging Face](https://huggingface.co) and pyannote:

1. Create a token at [hf.co/settings/tokens](https://hf.co/settings/tokens).
2. Accept the user conditions for:
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
3. Set the token when running:
   ```bash
   export HF_TOKEN=your_token_here
   pdm run meet
   ```
   Or use `HUGGING_FACE_HUB_TOKEN` instead of `HF_TOKEN`.

To enable diarization, pass the flag:
```bash
pdm run meet --diarization
```

## Usage

```bash
# Record and transcribe only (default)
pdm run meet

# Enable diarization and/or sentiment
pdm run meet --diarization
pdm run meet --sentiment
pdm run meet --diarization --sentiment

# Record audio only
pdm run record my-recording                    # With timestamp
pdm run record my-recording --no-timestamp     # Without timestamp
```

## Output

Creates a folder in `records/` with:

- Audio file (WAV → MP3)
- Transcription (TXT) with timestamps. With diarization and sentiment enabled, each line looks like:
  ```
  [0.00s -> 5.20s] Speaker_0 (positive): Hello everyone, thanks for joining.
  [5.20s -> 12.40s] Speaker_1 (neutral): Let's go through the agenda.
  ```
  With both disabled, the format is backwards compatible: `[start->end] text`.
