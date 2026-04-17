# Cover Letter Generator

AI-powered cover letter generator that runs as a **Claude Code slash command** — no API key needed, uses your Claude subscription.

## What it does

- Researches the company (recent news, culture, pain points) via web search
- Looks up the hiring manager if provided
- Analyzes the JD — extracts key skills and the core problem the role solves
- Maps your profile against the requirements
- Writes a unique, non-generic cover letter in your exact format
- Outputs a `.docx` ready to submit or edit

## Setup

```bash
# Install the one dependency needed for .docx output
pip install python-docx pyyaml

# Open Claude Code in this folder
cd ~/Desktop/coverletter-gen
claude
```

## Usage

Inside Claude Code, type:
```
/cover-letter
```

**First run** — Claude walks you through a one-time profile setup.

**Every run after:**
1. Paste a job URL or JD text (type `DONE` when finished pasting)
2. Claude auto-detects company, role, hiring manager from the JD
3. Confirm or correct in one line
4. Claude researches + generates → outputs `output/[Company]_[Role]_CoverLetter.docx`

## Works with

- ✅ Public job boards (Greenhouse, Lever, Indeed) — paste URL
- ✅ Login-required platforms (Handshake, LinkedIn, Workday) — paste JD text

## Project structure

```
.claude/
  commands/
    cover-letter.md   — slash command instructions
writer.py             — .docx builder (Times New Roman, page border, exact template)
writer_cli.py         — CLI wrapper called by the slash command
setup.py              — profile onboarding helper
profile.yaml          — your saved profile (gitignored)
output/               — generated cover letters (gitignored)
```

## Powered by

- Claude Code (your subscription — no API key needed)
- `python-docx` for Word output
