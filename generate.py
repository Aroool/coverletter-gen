"""
Core generation logic:
1. Fetch/parse job description (URL or raw text)
2. Research the company and hiring manager via web search
3. Send everything to Claude → get structured cover letter content
4. Pass to writer.py to produce the .docx
"""

import os
import re
import yaml
import json
from pathlib import Path
from datetime import date
from rich.console import Console
from rich.spinner import Spinner
import anthropic

console_default = Console()


def load_profile(profile_path: Path) -> dict:
    with open(profile_path) as f:
        return yaml.safe_load(f)


def profile_to_text(profile: dict) -> str:
    """Convert profile dict to a rich text block for Claude."""
    lines = []

    lines.append(f"NAME: {profile.get('name', '')}")
    lines.append(f"EMAIL: {profile.get('email', '')}")
    lines.append(f"PHONE: {profile.get('phone', '')}")
    lines.append(f"LINKEDIN: {profile.get('linkedin_url', '')}")
    lines.append(f"LOCATION: {profile.get('location', '')}")
    lines.append(f"TARGET ROLE: {profile.get('target_role', '')}")
    lines.append(f"YEARS OF EXPERIENCE: {profile.get('years_experience', '')}")
    lines.append(f"HEADLINE: {profile.get('headline', '')}")
    lines.append(f"WHAT MAKES ME UNIQUE: {profile.get('unique_value', '')}")

    edu = profile.get("education", {})
    if edu:
        gpa = f", GPA: {edu['gpa']}" if edu.get("gpa") else ""
        lines.append(f"EDUCATION: {edu.get('degree', '')} — {edu.get('school', '')} ({edu.get('year', '')}){gpa}")

    skills = profile.get("technical_skills", [])
    if skills:
        lines.append(f"TECHNICAL SKILLS: {', '.join(skills)}")

    if profile.get("soft_skills"):
        lines.append(f"SOFT SKILLS / WORKING STYLE: {profile['soft_skills']}")

    exp_list = profile.get("experience", [])
    if exp_list:
        lines.append("\nWORK EXPERIENCE:")
        for exp in exp_list:
            lines.append(f"  • {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')})")
            lines.append(f"    Summary: {exp.get('description', '')}")
            for ach in exp.get("achievements", []):
                lines.append(f"    - {ach}")

    proj_list = profile.get("projects", [])
    if proj_list:
        lines.append("\nPROJECTS:")
        for proj in proj_list:
            url_part = f" ({proj['url']})" if proj.get("url") else ""
            lines.append(f"  • {proj.get('name', '')}{url_part}")
            lines.append(f"    What: {proj.get('description', '')}")
            lines.append(f"    Impact: {proj.get('impact', '')}")
            lines.append(f"    Tech: {proj.get('tech', '')}")

    if profile.get("industries"):
        lines.append(f"TARGET INDUSTRIES: {profile['industries']}")
    if profile.get("availability"):
        lines.append(f"AVAILABILITY: {profile['availability']}")
    if profile.get("visa_status"):
        lines.append(f"VISA STATUS: {profile['visa_status']}")
    if profile.get("extra_bio"):
        lines.append(f"ADDITIONAL CONTEXT: {profile['extra_bio']}")

    return "\n".join(lines)


def research_and_generate(
    client: anthropic.Anthropic,
    profile_text: str,
    jd_input: str,
    company_name: str,
    role_title: str,
    hiring_manager: str,
    extra_context: str,
    console: Console,
) -> dict:
    """
    Uses Claude with web_search to:
    - Fetch JD if URL provided
    - Research company
    - Research hiring manager
    - Generate cover letter content
    Returns a dict with all the content needed by writer.py
    """

    is_url = jd_input.strip().startswith("http")

    hm_section = ""
    if hiring_manager:
        hm_section = f"""
Also search for information about the hiring manager: "{hiring_manager}" at {company_name}.
Find their background, what they've written or said publicly, their focus areas, anything that would
help personalize the letter toward them specifically.
"""

    system_prompt = """You are an expert cover letter writer. Your cover letters are:
- Direct and confident, never sycophantic or generic
- Deeply tailored to the specific company and role
- Written to show the candidate deeply understands the company's actual problems
- Under one page — tight, punchy paragraphs
- Opening with something unexpected and specific (NOT "I am writing to apply for...")

You will be given a candidate's full profile, a job description, and research context.
You must return a JSON object with the cover letter content. Nothing else — pure JSON."""

    user_prompt = f"""Here is the candidate's profile:

{profile_text}

---

Job Information:
- Company: {company_name}
- Role: {role_title}
- Hiring Manager: {hiring_manager if hiring_manager else "Unknown"}
- Extra context from candidate: {extra_context if extra_context else "None"}

---

{"JOB URL (fetch this): " + jd_input if is_url else "JOB DESCRIPTION:\n" + jd_input}

---

Your task:
1. {"Fetch the job description from the URL above." if is_url else "Use the job description provided above."}
2. Search the web for recent information about {company_name}: their mission, culture, recent news, what they're building, any pain points they're known for, recent hires, funding, product launches.
3. {hm_section if hiring_manager else "Search for the company's key leadership/hiring contacts if possible."}
4. Analyze the JD: extract the top 3-5 skills required, the core responsibilities, and the biggest problem this role is solving.
5. Map the candidate's experience and projects to those specific requirements.

Then generate the cover letter content and return this exact JSON:

{{
  "hiring_manager_name": "Full name or 'Hiring Manager' if unknown",
  "hiring_manager_title": "Their title if found, else ''",
  "company_research_summary": "2-3 sentences on what you found about the company (internal note, not in letter)",
  "hm_research_summary": "What you found about the hiring manager (internal note, not in letter)",
  "jd_key_skills": ["skill1", "skill2", "skill3"],
  "jd_core_problem": "What problem is this role solving at the company",
  "opening_hook": "First paragraph — unique, specific, NOT generic. Reference something real about the company or role. Should make the reader lean in.",
  "body_paragraphs": [
    "Second paragraph — connect candidate's most relevant experience/project directly to the role",
    "Third paragraph — show you understand their specific operational/business context and how you'd contribute",
    "Fourth paragraph — optional, only if needed to cover a critical skill or add a strong point. Leave empty string if not needed."
  ],
  "value_bullets": [
    "Specific thing you'd do / bring (max 4, each under 12 words)",
    "...",
    "...",
    "..."
  ],
  "closing_paragraph": "Final paragraph — forward-looking, confident, not begging. Show you're selective too.",
  "sign_off": "Sincerely"
}}

Rules:
- Opening hook must NOT start with "I am writing", "I am excited", "I am reaching out", or any generic opener
- Every paragraph must feel like it was written specifically for THIS company and THIS role
- Reference the candidate's real projects and achievements by name where relevant
- Keep total length to fit ONE page comfortably (3-4 short paragraphs + bullets)
- Be bold and direct — hiring managers read 100 generic letters a day
"""

    console.print("[dim]  → Fetching JD and researching company...[/dim]")

    # Use streaming with web search tool
    content_parts = []
    input_tokens = 0
    output_tokens = 0

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=system_prompt,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for event in stream:
            pass  # let stream complete

        response = stream.get_final_message()

    # Extract text content from response
    raw_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            raw_text += block.text

    console.print("[dim]  → Parsing response...[/dim]")

    # Extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if not json_match:
        raise ValueError(f"Could not extract JSON from Claude response.\n\nRaw response:\n{raw_text[:500]}")

    result = json.loads(json_match.group())

    # Log research findings
    if result.get("company_research_summary"):
        console.print(f"[dim]  ✓ Company: {result['company_research_summary'][:80]}...[/dim]")
    if result.get("hm_research_summary"):
        console.print(f"[dim]  ✓ Hiring Manager: {result['hm_research_summary'][:80]}...[/dim]")
    if result.get("jd_core_problem"):
        console.print(f"[dim]  ✓ Role problem: {result['jd_core_problem'][:80]}...[/dim]")

    return result


def generate_cover_letter(
    profile_path: Path,
    jd_input: str,
    company_name: str,
    role_title: str,
    hiring_manager: str,
    extra_context: str,
    output_dir: Path,
    console: Console = None,
) -> str:
    """Main entry point. Returns path to generated .docx file."""

    if console is None:
        console = console_default

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]ANTHROPIC_API_KEY environment variable not set.[/red]")
        console.print("[dim]Run: export ANTHROPIC_API_KEY=your_key_here[/dim]")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    profile = load_profile(profile_path)
    profile_text = profile_to_text(profile)

    # Research + generate content
    content = research_and_generate(
        client=client,
        profile_text=profile_text,
        jd_input=jd_input,
        company_name=company_name,
        role_title=role_title,
        hiring_manager=hiring_manager,
        extra_context=extra_context,
        console=console,
    )

    console.print("[dim]  → Building .docx...[/dim]")

    # Build the .docx
    from writer import build_docx

    today = date.today()
    safe_company = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
    safe_role = re.sub(r'[^\w\s-]', '', role_title).strip().replace(' ', '_')
    filename = f"{safe_company}_{safe_role}_CoverLetter.docx"
    output_path = output_dir / filename

    build_docx(
        profile=profile,
        content=content,
        company_name=company_name,
        role_title=role_title,
        today=today,
        output_path=output_path,
    )

    return str(output_path)
