"""
CLI module — Typer-based command-line interface for byeGPT.

Usage:
    byegpt convert --input export.zip --output ./gemini_history --split-size 7MB
    byegpt persona --input export.zip --output ./digital_passport.md
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt

from byegpt import __version__
from byegpt.parser import load_conversations, extract_attachments
from byegpt.formatter import write_split_files
from byegpt.persona import generate_persona, extract_topics, extract_subtopics

app = typer.Typer(
    name="byegpt",
    help="🚀 Convert ChatGPT exports to Gemini-optimized Markdown.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def _parse_size(size_str: str) -> float:
    """Parse a size string like '7MB' or '10mb' into megabytes."""
    match = re.match(r"^(\d+(?:\.\d+)?)\s*(MB|mb|Mb)?$", size_str.strip())
    if not match:
        raise typer.BadParameter(
            f"Invalid size format: '{size_str}'. Use format like '7MB' or '10MB'."
        )
    return float(match.group(1))


def _find_default_input() -> Path:
    """Auto-detect conversations.json or an export ZIP in the current directory."""
    # First priority: conversations.json
    if Path("conversations.json").exists():
        return Path("conversations.json")
    
    # Second priority: any zip file that looks like a ChatGPT export
    for zip_file in Path(".").glob("*.zip"):
        return zip_file

    raise typer.BadParameter(
        "Could not find 'conversations.json' or a ChatGPT export .zip in the "
        "current directory. Please provide an input file using --input."
    )


def version_callback(value: bool) -> None:
    if value:
        rprint(f"[bold cyan]byeGPT[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """🚀 byeGPT — Migrate your ChatGPT history to Gemini."""
    pass


@app.command()
def convert(
    input_path: Optional[Path] = typer.Option(
        None,
        "--input", "-i",
        help="Path to ChatGPT export (.zip or conversations.json). Auto-detected if omitted.",
        exists=True,
    ),
    output_dir: Path = typer.Option(
        Path("./gemini_history"),
        "--output", "-o",
        help="Output folder for Markdown files.",
    ),
    split_size: str = typer.Option(
        "7MB",
        "--split-size", "-s",
        help="Max file size per Markdown file (e.g., '7MB', '10MB').",
    ),
    no_thinking: bool = typer.Option(
        False,
        "--no-thinking",
        help="Exclude thinking/reasoning blocks from output.",
    ),
    no_attachments: bool = typer.Option(
        False,
        "--no-attachments",
        help="Skip attachment extraction.",
    ),
    organize: bool = typer.Option(
        False,
        "--organize",
        help="Interactively select topics to organize conversations into subfolders.",
    ),
) -> None:
    """
    Convert a ChatGPT export to Gemini-optimized Markdown files.

    Supports auto-detecting conversations.json or .zip files in the current folder.
    """
    if input_path is None:
        input_path = _find_default_input()
        
    max_mb = _parse_size(split_size)

    console.print(
        Panel.fit(
            f"[bold cyan]byeGPT[/bold cyan] v{__version__}\n"
            f"[dim]Converting ChatGPT → Gemini Markdown[/dim]",
            border_style="cyan",
        )
    )

    # Load conversations
    with console.status("[bold green]Loading conversations..."):
        start = time.time()
        conversations, zf = load_conversations(input_path)
        load_time = time.time() - start

    console.print(
        f"  ✅ Loaded [bold]{len(conversations):,}[/bold] conversations "
        f"in {load_time:.1f}s"
    )

    # ── Interactive Topic + Subtopic Selection ───────────────────────
    # topic_tree is None (flat mode) or a dict: {topic: [sub1, sub2, sub3]}
    topic_tree: dict[str, list[str]] | None = None
    if organize:
        console.print("\n[bold cyan]🧠 Step 1 — Topic Analysis[/bold cyan]")
        with console.status("Extracting top topics from your history..."):
            top_topics = extract_topics(conversations, top_n=15)

        if top_topics:
            console.print("Here are the top topics from your conversations:\n")
            for idx, (word, count) in enumerate(top_topics, 1):
                console.print(f"  [bold]{idx:>2}.[/bold] [yellow]{word}[/yellow] ({count} convos)")

            console.print("\n[dim]Enter the topics you want as folders (comma-separated).[/dim]")
            console.print("[dim]Or type 'all' to use all of them. Press Enter to skip.[/dim]")

            user_input = Prompt.ask("Topics to keep")

            selected: list[str] = []
            if user_input.strip().lower() == "all":
                selected = [t[0] for t in top_topics]
            elif user_input.strip():
                selected = [t.strip().lower() for t in user_input.split(",") if t.strip()]

            if selected:
                # ── Step 2: Subtopic refinement ──────────────────────
                console.print(f"\n[bold cyan]🔍 Step 2 — Subtopic Refinement[/bold cyan]")
                with console.status("Analyzing subtopics for each selected topic..."):
                    subtopics_map = extract_subtopics(conversations, selected, top_n=3)

                topic_tree = {}
                for topic in selected:
                    subs = subtopics_map.get(topic, [])
                    if subs:
                        sub_display = ", ".join(f"[green]{w}[/green] ({c})" for w, c in subs)
                        console.print(f"\n  📂 [bold yellow]{topic}[/bold yellow] → {sub_display}")
                    else:
                        console.print(f"\n  📂 [bold yellow]{topic}[/bold yellow] → [dim]no subtopics found[/dim]")
                    topic_tree[topic] = [w for w, _ in subs]

                console.print("\n[dim]Press Enter to confirm this structure, or type 'flat' for no subtopics.[/dim]")
                confirm = Prompt.ask("Confirm", default="yes")

                if confirm.strip().lower() == "flat":
                    # Downgrade to flat topic folders (no subtopics)
                    topic_tree = {t: [] for t in selected}
                    console.print("  📂 Using flat topic folders (no subtopics).")
                else:
                    total_folders = sum(max(1, len(subs)) for subs in topic_tree.values()) + 1  # +1 for Uncategorized
                    console.print(f"  ✅ Will organize into ~{total_folders} subfolders.")
        else:
            console.print("[yellow]Could not extract enough topics to organize.[/yellow]")

    # Extract attachments
    attachment_map: dict[str, str] = {}
    if not no_attachments and zf is not None:
        with console.status("[bold green]Extracting attachments..."):
            start = time.time()
            attachment_map = extract_attachments(zf, conversations, output_dir)
            att_time = time.time() - start

        console.print(
            f"  ✅ Extracted [bold]{len(attachment_map):,}[/bold] attachments "
            f"to [cyan]{output_dir / 'assets'}[/cyan] in {att_time:.1f}s"
        )

    # Convert to Markdown with progress bar
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Converting conversations...",
            total=len(conversations),
        )

        def update_progress(count: int) -> None:
            progress.update(task, completed=count)

        start = time.time()
        created_files = write_split_files(
            conversations=conversations,
            output_dir=output_dir,
            max_size_mb=max_mb,
            attachment_map=attachment_map,
            include_thinking=not no_thinking,
            progress_callback=update_progress,
            topic_tree=topic_tree,
        )
        convert_time = time.time() - start

    # Close ZIP if open
    if zf is not None:
        zf.close()

    # Summary
    console.print()
    console.print(
        Panel.fit(
            f"[bold green]✅ Migration complete![/bold green]\n\n"
            f"  📁 Output folder:  [cyan]{output_dir}[/cyan]\n"
            f"  📄 Files created:  [bold]{len(created_files)}[/bold]\n"
            f"  📎 Attachments:    [bold]{len(attachment_map):,}[/bold]\n"
            f"  📏 Max file size:  {max_mb}MB\n"
            f"  ⏱️  Total time:     {convert_time:.1f}s\n"
            f"  💭 Thinking blocks: {'excluded' if no_thinking else 'included'}",
            title="[bold]Summary[/bold]",
            border_style="green",
        )
    )


@app.command()
def persona(
    input_path: Optional[Path] = typer.Option(
        None,
        "--input", "-i",
        help="Path to ChatGPT export (.zip or conversations.json). Auto-detected if omitted.",
        exists=True,
    ),
    output_file: Path = typer.Option(
        Path("./digital_passport.md"),
        "--output", "-o",
        help="Output file path for the Digital Passport.",
    ),
) -> None:
    """
    Generate a Digital Passport — a persona document that captures your
    communication style, interests, and patterns from your ChatGPT history.

    Supports auto-detecting conversations.json or .zip files in the current folder.
    """
    if input_path is None:
        input_path = _find_default_input()
        
    console.print(
        Panel.fit(
            f"[bold cyan]byeGPT[/bold cyan] v{__version__}\n"
            f"[dim]Generating Digital Passport[/dim]",
            border_style="cyan",
        )
    )

    # Load conversations
    with console.status("[bold green]Loading conversations..."):
        conversations, zf = load_conversations(input_path)

    if zf is not None:
        zf.close()

    console.print(
        f"  ✅ Loaded [bold]{len(conversations):,}[/bold] conversations"
    )

    # Generate persona
    with console.status("[bold green]Analyzing your history..."):
        start = time.time()
        passport_md = generate_persona(conversations)
        gen_time = time.time() - start

    # Write output
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(passport_md, encoding="utf-8")

    console.print()
    console.print(
        Panel.fit(
            f"[bold green]🛂 Digital Passport created![/bold green]\n\n"
            f"  📄 File: [cyan]{output_file}[/cyan]\n"
            f"  📊 Based on: [bold]{len(conversations):,}[/bold] conversations\n"
            f"  ⏱️  Generated in: {gen_time:.1f}s\n\n"
            f"  [dim]Tip: Share this file with Gemini to get personalized responses![/dim]",
            title="[bold]Summary[/bold]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()
