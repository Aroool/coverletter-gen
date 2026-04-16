"""
Profile setup — one-time structured questions that build your profile.yaml.
The richer this is, the better every cover letter will be.
"""

import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

console = Console()


def ask(prompt: str, default: str = "", required: bool = True) -> str:
    """Ask a question, repeat if required and empty."""
    while True:
        val = Prompt.ask(prompt, default=default).strip()
        if val or not required:
            return val
        console.print("[red]This field is required.[/red]")


def ask_multiline(prompt: str, hint: str = "Press Enter on empty line when done") -> str:
    """Collect multi-line input."""
    console.print(f"[bold]{prompt}[/bold] [dim]({hint})[/dim]")
    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
            console.print("[dim]Enter at least one line.[/dim]")
        else:
            lines.append(line)
    return "\n".join(lines)


def ask_list(prompt: str, hint: str = "One per line. Press Enter on empty line when done") -> list:
    """Collect a list of items."""
    console.print(f"[bold]{prompt}[/bold] [dim]({hint})[/dim]")
    items = []
    while True:
        item = input().strip()
        if item == "":
            if items:
                break
            console.print("[dim]Enter at least one item.[/dim]")
        else:
            items.append(item)
    return items


def collect_experiences() -> list:
    """Collect work experience entries."""
    experiences = []
    console.print("\n[bold]Work Experience[/bold] [dim](Enter each role — most recent first)[/dim]")

    while True:
        console.print(f"\n[cyan]Role #{len(experiences) + 1}[/cyan]")
        exp = {
            "company": ask("  Company name"),
            "title": ask("  Your job title"),
            "duration": ask("  Duration (e.g. Jan 2023 – Present)"),
            "description": ask("  One-line summary of what you did"),
        }

        console.print("  [bold]Key achievements[/bold] [dim](quantified if possible — one per line, Enter on empty to finish)[/dim]")
        achievements = []
        while True:
            a = input("  → ").strip()
            if a == "":
                if achievements:
                    break
                console.print("  [dim]Add at least one achievement.[/dim]")
            else:
                achievements.append(a)
        exp["achievements"] = achievements
        experiences.append(exp)

        if not Confirm.ask("\n  Add another role?", default=True):
            break

    return experiences


def collect_projects() -> list:
    """Collect project entries."""
    projects = []
    console.print("\n[bold]Projects[/bold] [dim](Things you've built — side projects, open source, etc.)[/dim]")

    while True:
        console.print(f"\n[cyan]Project #{len(projects) + 1}[/cyan]")
        proj = {
            "name": ask("  Project name"),
            "url": ask("  URL (or press Enter to skip)", required=False),
            "description": ask("  What is it? What problem does it solve?"),
            "impact": ask("  What's the impact / result?"),
            "tech": ask("  Tech stack used (e.g. Python, React, Claude API)"),
        }
        projects.append(proj)

        if not Confirm.ask("\n  Add another project?", default=True):
            break

    return projects


def run_setup(profile_path: Path, editing: bool = False):
    """Run the full profile setup questionnaire."""

    existing = {}
    if editing and profile_path.exists():
        with open(profile_path) as f:
            existing = yaml.safe_load(f) or {}

    console.print(Panel(
        "[bold]Profile Setup[/bold]\n\n"
        "This is saved locally and used to personalize every cover letter.\n"
        "[dim]The more detail you add, the better the output.[/dim]",
        border_style="cyan"
    ))

    profile = {}

    # ── Personal Info ──────────────────────────────────────────────────────────
    console.print("\n[bold underline]1. Personal Info[/bold underline]")
    profile["name"] = ask("Full name", default=existing.get("name", ""))
    profile["email"] = ask("Email", default=existing.get("email", ""))
    profile["phone"] = ask("Phone", default=existing.get("phone", ""))
    profile["linkedin_url"] = ask("LinkedIn URL", default=existing.get("linkedin_url", ""))
    profile["location"] = ask("Location (e.g. Boston, MA)", default=existing.get("location", ""))

    # ── Career Summary ─────────────────────────────────────────────────────────
    console.print("\n[bold underline]2. Career Summary[/bold underline]")
    profile["target_role"] = ask(
        "What role/type of job are you targeting?",
        default=existing.get("target_role", "")
    )
    profile["years_experience"] = ask(
        "Years of total experience",
        default=existing.get("years_experience", "")
    )
    profile["headline"] = ask(
        "Your professional headline (1 sentence — how you'd describe yourself)",
        default=existing.get("headline", "")
    )
    profile["unique_value"] = ask(
        "What makes you different from other candidates? (Be honest and specific)",
        default=existing.get("unique_value", "")
    )

    # ── Education ─────────────────────────────────────────────────────────────
    console.print("\n[bold underline]3. Education[/bold underline]")
    edu = existing.get("education", {})
    profile["education"] = {
        "degree": ask("Degree (e.g. MS Computer Science)", default=edu.get("degree", "")),
        "school": ask("School / University", default=edu.get("school", "")),
        "year": ask("Graduation year", default=edu.get("year", "")),
        "gpa": ask("GPA (optional, press Enter to skip)", default=edu.get("gpa", ""), required=False),
    }

    # ── Skills ────────────────────────────────────────────────────────────────
    console.print("\n[bold underline]4. Skills[/bold underline]")
    console.print("[dim]Be specific — not just 'Python' but 'Python (FastAPI, async, data pipelines)'[/dim]")

    if editing and existing.get("technical_skills"):
        console.print(f"[dim]Current: {', '.join(existing['technical_skills'])}[/dim]")
        if Confirm.ask("Keep existing skills?", default=True):
            profile["technical_skills"] = existing["technical_skills"]
        else:
            profile["technical_skills"] = ask_list("Technical skills")
    else:
        profile["technical_skills"] = ask_list("Technical skills")

    profile["soft_skills"] = ask(
        "Top soft skills / working style (1-2 sentences)",
        default=existing.get("soft_skills", "")
    )

    # ── Work Experience ───────────────────────────────────────────────────────
    console.print("\n[bold underline]5. Work Experience[/bold underline]")
    if editing and existing.get("experience"):
        console.print("[dim]You have existing experience entries.[/dim]")
        if Confirm.ask("Re-enter work experience?", default=False):
            profile["experience"] = collect_experiences()
        else:
            profile["experience"] = existing["experience"]
    else:
        profile["experience"] = collect_experiences()

    # ── Projects ─────────────────────────────────────────────────────────────
    console.print("\n[bold underline]6. Projects[/bold underline]")
    if editing and existing.get("projects"):
        console.print("[dim]You have existing project entries.[/dim]")
        if Confirm.ask("Re-enter projects?", default=False):
            profile["projects"] = collect_projects()
        else:
            profile["projects"] = existing["projects"]
    else:
        profile["projects"] = collect_projects()

    # ── Additional Context ────────────────────────────────────────────────────
    console.print("\n[bold underline]7. Additional Context[/bold underline]")
    profile["industries"] = ask(
        "Industries you're targeting (e.g. FinTech, Healthcare, SaaS)",
        default=existing.get("industries", ""),
        required=False
    )
    profile["availability"] = ask(
        "Availability (e.g. 2 weeks notice, immediate)",
        default=existing.get("availability", "immediate"),
        required=False
    )
    profile["visa_status"] = ask(
        "Visa / work authorization status (optional)",
        default=existing.get("visa_status", ""),
        required=False
    )
    profile["extra_bio"] = ask(
        "Anything else about you that should inform cover letters? (optional)",
        default=existing.get("extra_bio", ""),
        required=False
    )

    # Save
    with open(profile_path, "w") as f:
        yaml.dump(profile, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return profile
