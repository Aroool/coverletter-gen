#!/usr/bin/env python3
"""
Cover Letter Generator
Researches companies & hiring managers, then crafts a personalized cover letter
in your exact format — output as a ready-to-submit .docx file.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

BASE_DIR = Path(__file__).parent
PROFILE_FILE = BASE_DIR / "profile.yaml"
OUTPUT_DIR = BASE_DIR / "output"

console = Console()


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]Cover Letter Generator[/bold cyan]\n"
        "[dim]AI-powered · Personalized · Ready to submit[/dim]",
        border_style="cyan"
    ))

    # First run — profile setup
    if not PROFILE_FILE.exists():
        console.print("\n[yellow]No profile found. Let's set you up first — this is a one-time thing.[/yellow]\n")
        from setup import run_setup
        run_setup(PROFILE_FILE)
        console.print("\n[green]Profile saved![/green] You can edit it anytime at [cyan]profile.yaml[/cyan]\n")

    # Offer to edit profile
    else:
        edit = Confirm.ask("[dim]Edit your profile before generating?[/dim]", default=False)
        if edit:
            from setup import run_setup
            run_setup(PROFILE_FILE, editing=True)
            console.print("\n[green]Profile updated.[/green]\n")

    # Collect job info
    console.print("[bold]Job Details[/bold]")
    console.print("[dim]Paste a job URL or the full job description. Press Enter twice when done.[/dim]\n")

    jd_input = Prompt.ask("Job URL or paste JD (URL preferred)")

    company_name = Prompt.ask("Company name")
    role_title = Prompt.ask("Role / Job title")
    hiring_manager = Prompt.ask("Hiring manager name [dim](press Enter to skip)[/dim]", default="")
    extra_context = Prompt.ask(
        "Any extra context? [dim](e.g. referral, something you know about the company)[/dim]",
        default=""
    )

    console.print("\n[cyan]Researching company, analyzing JD, and crafting your letter...[/cyan]\n")

    from generate import generate_cover_letter

    result = generate_cover_letter(
        profile_path=PROFILE_FILE,
        jd_input=jd_input,
        company_name=company_name,
        role_title=role_title,
        hiring_manager=hiring_manager,
        extra_context=extra_context,
        output_dir=OUTPUT_DIR,
        console=console,
    )

    if result:
        console.print(Panel.fit(
            f"[bold green]Done![/bold green]\n\n"
            f"[cyan]{result}[/cyan]\n\n"
            f"[dim]Open, review, and submit. Edit freely — it's a Word doc.[/dim]",
            border_style="green"
        ))
    else:
        console.print("[red]Something went wrong. Check your API key and try again.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
