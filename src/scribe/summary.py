import pathlib

import typer
from ollama import chat

RECORDS_ROOT = pathlib.Path(__file__).parent.parent.parent / "records"

SUMMARY_PROMPT = """You are an assistant that summarizes meeting transcripts. Given the following transcript, provide:
If the meeting is too short, you may just say: "This meeting was too short to summarize." And nothing else.
1) A brief summary (2–3 paragraphs).
2) Key takeaways (bullet list).
3) Next action items (bullet list).

Use markdown with headings: ## Summary, ## Key takeaways, ## Next action items."""


def _resolve_transcript_path(path: pathlib.Path | None) -> pathlib.Path:
    """Resolve to a transcript .txt file. If path is None, use latest in records/."""
    if path is not None:
        p = path.resolve()
        if p.is_dir():
            # Find .txt in dir with same stem as dir name
            candidate = p / f"{p.name}.txt"
            if candidate.exists():
                return candidate
            # Fallback: any .txt in dir
            for f in p.iterdir():
                if f.suffix == ".txt":
                    return f
            raise typer.BadParameter(f"No transcript .txt found in directory: {p}")
        if p.exists():
            return p
        raise typer.BadParameter(f"Path does not exist: {p}")

    # Default: latest transcript under records/
    if not RECORDS_ROOT.exists():
        raise typer.Exit(
            typer.echo(
                "No records directory found. Run a meeting first (pdm run meet).",
                err=True,
            )
            or 1
        )
    transcripts = []
    for meeting_dir in RECORDS_ROOT.iterdir():
        if not meeting_dir.is_dir():
            continue
        txt = meeting_dir / f"{meeting_dir.name}.txt"
        if txt.exists():
            transcripts.append(txt)
    if not transcripts:
        raise typer.Exit(
            typer.echo(
                "No transcripts found in records/. Run a meeting first (pdm run meet).",
                err=True,
            )
            or 1
        )
    transcripts.sort(key=lambda p: p.name)
    return transcripts[-1]


def _read_transcript(transcript_path: pathlib.Path) -> str:
    """Read transcript file and return full text (with timestamps)."""
    return transcript_path.read_text(encoding="utf-8", errors="replace")


def _generate_summary(transcript_text: str, model: str) -> str:
    """Call Ollama to generate summary, key takeaways, and next action items."""
    try:
        response = chat(
            model=model,
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": f"Transcript:\n\n{transcript_text}"},
            ],
        )
    except Exception as e:
        raise typer.Exit(
            typer.echo(
                f"Ollama error: {e}\nIs Ollama running at the configured endpoint?",
                err=True,
            )
            or 1
        )
    content = response.get("message", {}).get("content", "")
    if not content:
        raise typer.Exit(
            typer.echo("Ollama returned an empty response.", err=True) or 1
        )
    return content


app = typer.Typer()


@app.command()
def summary(
    path: pathlib.Path | None = typer.Argument(
        None,
        help="Path to transcript file or meeting directory. Default: latest in records/.",
        exists=False,
    ),
    model: str = typer.Option(
        "tinyllama",
        "--model",
        "-m",
        help="Ollama model to use for summarization (default fits ~1GB; use gemma2 etc. if you have more memory).",
    ),
):
    """
    Generate a summary, key takeaways, and next action items from a transcript using Ollama.
    Writes summary.md in the same folder as the transcript and prints to stdout.
    """
    transcript_path = _resolve_transcript_path(path)
    transcript_text = _read_transcript(transcript_path)
    summary_text = _generate_summary(transcript_text, model)

    out_path = transcript_path.parent / "summary.md"
    out_path.write_text(summary_text, encoding="utf-8")
    typer.echo(f"Wrote {out_path}")
    typer.echo(summary_text)


if __name__ == "__main__":
    app()
