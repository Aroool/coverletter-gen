#!/usr/bin/env python3
"""
CLI wrapper for writer.py.
Called by the Claude Code slash command after generating cover letter content.

Usage:
    python3 writer_cli.py /tmp/cl_content.json
"""

import sys
import json
import yaml
import re
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).parent
PROFILE_FILE = BASE_DIR / "profile.yaml"
OUTPUT_DIR = BASE_DIR / "output"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 writer_cli.py <content_json_path>")
        sys.exit(1)

    content_path = Path(sys.argv[1])
    if not content_path.exists():
        print(f"Error: {content_path} not found")
        sys.exit(1)

    if not PROFILE_FILE.exists():
        print(f"Error: profile.yaml not found at {PROFILE_FILE}")
        sys.exit(1)

    # Load inputs
    with open(content_path) as f:
        content = json.load(f)

    with open(PROFILE_FILE) as f:
        profile = yaml.safe_load(f)

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Build filename
    company = content.get("company_name", "Company")
    role    = content.get("role_title", "Role")
    safe_company = re.sub(r'[^\w\s-]', '', company).strip().replace(' ', '_')
    safe_role    = re.sub(r'[^\w\s-]', '', role).strip().replace(' ', '_')
    filename = f"{safe_company}_{safe_role}_CoverLetter.docx"
    output_path = OUTPUT_DIR / filename

    # Generate
    from writer import build_docx
    build_docx(
        profile=profile,
        content=content,
        company_name=company,
        role_title=role,
        today=date.today(),
        output_path=output_path,
    )

    print(f"✓ Cover letter saved to: {output_path}")


if __name__ == "__main__":
    main()
