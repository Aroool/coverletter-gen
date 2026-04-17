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

# Platforms that require login — can't be fetched by web search
GATED_PLATFORMS = {
    "app.joinhandshake.com": "Handshake",
    "handshake.com": "Handshake",
    "linkedin.com/jobs": "LinkedIn Jobs",
    "workday.com": "Workday",
    "myworkdayjobs.com": "Workday",
    "wd1.myworkdayjobs.com": "Workday",
    "wd3.myworkdayjobs.com": "Workday",
    "boards.greenhouse.io": None,   # usually public — allow
    "jobs.lever.co": None,          # usually public — allow
    "indeed.com": None,             # usually public — allow
}


def detect_gated_url(url: str) -> str | None:
    """Return platform name if URL is login-protected, else None."""
    url_lower = url.lower()
    for domain, platform_name in GATED_PLATFORMS.items():
        if domain in url_lower and platform_name is not None:
            return platform_name
    return None


def collect_multiline(console: Console, prompt_text: str) -> str:
    """
    Reliable multi-line input for terminal paste.
    User pastes text, then types DONE on a new line and hits Enter.
    This avoids zsh interpreting pasted lines as shell commands.
    """
    console.print(f"\n[dim]{prompt_text}[/dim]")
    console.print("[bold yellow]When finished, type DONE on a new line and press Enter:[/bold yellow]\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == "DONE":
            break
        lines.append(line)

    return "\n".join(lines)


def collect_jd(console: Console) -> str:
    """
    Smart JD collector:
    - If user pastes a public URL  → fetch via web search
    - If user pastes a gated URL   → ask them to paste JD text
    - If user pastes raw JD text   → auto-detects and collects full multi-line paste
    """
    console.print("[bold]Job Details[/bold]")
    console.print("[dim]Options:[/dim]")
    console.print("[dim]  • Paste a job URL (public boards like Greenhouse, Lever, Indeed)[/dim]")
    console.print("[dim]  • Paste JD text directly (for Handshake, LinkedIn, Workday)[/dim]")
    console.print("[dim]  → In both cases: paste, then type DONE on a new line and press Enter[/dim]\n")

    first_line = Prompt.ask("Job URL or first line of JD").strip()

    # ── URL path ──────────────────────────────────────────────────────────────
    if first_line.startswith("http"):
        gated = detect_gated_url(first_line)
        if not gated:
            # Public URL — Claude will fetch it
            console.print(f"[green]✓ URL captured — will fetch during generation.[/green]\n")
            return first_line
        else:
            # Gated URL — need JD text
            console.print(f"\n[yellow]⚠  {gated} requires login — can't fetch automatically.[/yellow]")
            console.print("[dim]Go back to the job page, copy all the JD text (Cmd+A → Cmd+C), paste below.[/dim]")
            jd_input = collect_multiline(console, "Paste the full job description:")
    else:
        # ── Raw JD text path ──────────────────────────────────────────────────
        # First line already captured — collect the rest
        console.print("[dim]Got it — keep pasting, then type DONE on a new line and press Enter:[/dim]")
        remaining_lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip().upper() == "DONE":
                break
            remaining_lines.append(line)

        jd_input = first_line
        if remaining_lines:
            jd_input = first_line + "\n" + "\n".join(remaining_lines)

    if not jd_input.strip():
        console.print("[red]No JD text entered. Exiting.[/red]")
        sys.exit(1)

    console.print(f"\n[green]✓ Captured {len(jd_input.split())} words of JD.[/green]\n")
    return jd_input

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

    # Collect JD
    jd_input = collect_jd(console)

    # Auto-extract company, role, hiring manager from JD
    import os
    import anthropic as _anthropic
    from generate import extract_jd_metadata, generate_cover_letter

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=your_key[/red]")
        sys.exit(1)

    _client = _anthropic.Anthropic(api_key=api_key)

    if not jd_input.startswith("http"):
        console.print("[dim]  → Reading JD...[/dim]")
        meta = extract_jd_metadata(_client, jd_input)
    else:
        meta = {"company_name": "", "role_title": "", "hiring_manager": ""}

    company_name  = meta.get("company_name", "")
    role_title    = meta.get("role_title", "")
    hiring_manager = meta.get("hiring_manager", "")

    # Show what was detected — let user correct inline if wrong
    console.print(f"\n[bold]Detected from JD:[/bold]")
    console.print(f"  Company  : [cyan]{company_name or '(not found)'}[/cyan]")
    console.print(f"  Role     : [cyan]{role_title or '(not found)'}[/cyan]")
    console.print(f"  HM       : [cyan]{hiring_manager or '(not found)'}[/cyan]")
    console.print("[dim]Press Enter to confirm each, or type a correction:[/dim]\n")

    company_name   = Prompt.ask("  Company",        default=company_name)
    role_title     = Prompt.ask("  Role",           default=role_title)
    hiring_manager = Prompt.ask("  Hiring manager", default=hiring_manager)

    console.print("\n[cyan]Researching company, analyzing JD, and crafting your letter...[/cyan]\n")

    result = generate_cover_letter(
        profile_path=PROFILE_FILE,
        jd_input=jd_input,
        company_name=company_name,
        role_title=role_title,
        hiring_manager=hiring_manager,
        extra_context="",
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
