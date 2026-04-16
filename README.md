# Cover Letter Generator

AI-powered cover letter generator that researches companies, understands job descriptions, and writes personalized letters — output as a ready-to-submit `.docx`.

## What it does

- Researches the company (recent news, culture, pain points) via web search
- Looks up the hiring manager if provided
- Analyzes the job description — extracts key skills and the core problem the role solves
- Maps your profile against the requirements
- Writes a unique, non-generic cover letter in your exact format
- Outputs a `.docx` ready to submit or edit

## Setup

```bash
# Install dependencies
pip install anthropic python-docx rich pyyaml

# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here

# Run
python3 main.py
```

## Usage

**First run** — walks you through a one-time profile setup (name, skills, experience, projects, achievements).

**Every run after:**
1. Paste a job URL or the full job description
2. Enter the company name and role title
3. Optionally add the hiring manager's name
4. Get a `[Company]_[Role]_CoverLetter.docx` in the `output/` folder

## Project structure

```
main.py      — CLI entry point
setup.py     — Structured profile onboarding
generate.py  — Claude + web research + letter generation
writer.py    — Builds the .docx in the correct format
output/      — Generated cover letters (gitignored)
profile.yaml — Your saved profile (gitignored)
```

## Powered by

- [Claude](https://anthropic.com) (claude-opus-4-6) with web search
- `python-docx` for Word output
- `rich` for CLI formatting
