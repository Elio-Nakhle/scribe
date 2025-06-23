import time
from faster_whisper import WhisperModel


def transcribe(audio_file, meeting_name):
    start_time = time.time()

    model = WhisperModel("turbo", device="cpu")
    segments, info = model.transcribe(audio_file, beam_size=5, vad_filter=True)

    print(
        "Detected language '%s' with probability %f"
        % (info.language, info.language_probability)
    )

    lines = []

    for segment in segments:
        line = "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
        print(line)
        lines.append(line)

    with open(meeting_name + ".txt", "w") as file:
        for line in lines:
            file.write(f"{line}\n")

    print(f"Transcription took: {time.time() - start_time} seconds")
