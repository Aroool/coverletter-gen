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


def extract_jd_metadata(client: anthropic.Anthropic, jd_text: str) -> dict:
    """
    Quickly extract company name, role title, and hiring manager
    from raw JD text using a fast, cheap Claude call.
    """
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"""Extract the following from this job description and return ONLY valid JSON:
{{
  "company_name": "company name (string)",
  "role_title": "exact job title (string)",
  "hiring_manager": "hiring manager full name if explicitly mentioned, else empty string"
}}

Job description:
{jd_text[:3000]}"""
        }]
    )
    raw = response.content[0].text.strip()
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        return json.loads(match.group())
    return {"company_name": "", "role_title": "", "hiring_manager": ""}


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

    system_prompt = """You are a world-class cover letter writer — part strategist, part copywriter.
You have read thousands of cover letters and you know exactly why most of them fail:
they are generic, self-focused, and written to impress rather than to connect.

Your letters do the opposite. They:
- Open with a line that makes the hiring manager stop and actually read
- Show the candidate understands the company's REAL problems — not the polished mission statement version
- Use the candidate's actual work as proof, not claims
- Sound like a sharp human wrote it at midnight after researching the company for 2 hours
- Never beg, never flatter, never use corporate filler words

You will be given a candidate profile, a job description, and research you will conduct.
You must return ONLY a valid JSON object — no explanation, no markdown, no preamble."""

    user_prompt = f"""CANDIDATE PROFILE:
{profile_text}

---

JOB TARGET:
- Company: {company_name}
- Role: {role_title}
- Hiring Manager: {hiring_manager if hiring_manager else "Unknown — research and find if possible"}
- Candidate's extra context: {extra_context if extra_context else "None provided"}

---

{"JOB POSTING URL — fetch this first: " + jd_input if is_url else "JOB DESCRIPTION (provided directly):\n" + jd_input}

---

RESEARCH PHASE — do all of this before writing a single word:

1. {"Fetch and read the full job description from the URL above." if is_url else "Read the job description carefully."}

2. Search for {company_name} and find:
   - What they actually do (not the PR version — the real product/service)
   - Their current stage (early startup? scaling? enterprise?)
   - Any recent news: funding rounds, product launches, pivots, layoffs, expansions
   - Their tech stack or operational model if visible
   - What kind of people they hire and what they value
   - Any pain points, challenges, or bold bets they are making
   - What they are proud of (check their blog, LinkedIn, press)

3. {"Search for '" + hiring_manager + "' at " + company_name + " — find their LinkedIn, any talks or articles they have written, their professional background, what they care about, their tone. Use this to write toward THEM specifically." if hiring_manager else "Search for the company's key decision-makers, engineering/product leadership, or whoever likely reviews this role. Note what you find."}

4. From the JD, extract:
   - The 3-5 non-negotiable skills or experiences they are looking for
   - The core problem this role is hired to solve (not the job title — the actual problem)
   - Any language or phrases the company repeats (signals their values)
   - Green flags in the JD that suggest company culture

5. Map the candidate's profile to the JD:
   - Which of their projects or experiences directly addresses the core problem?
   - What makes them a stronger fit than a generic candidate?
   - Is there anything in their profile that is unexpectedly relevant?

---

WRITING RULES — internalize these before generating:

OPENING HOOK (most important paragraph):
- Must NOT start with: "I", "My name", "I am writing", "I am excited", "I am applying", "I have always", "I recently", "I came across"
- Must NOT be a compliment to the company ("Your innovative approach...")
- Start with an INSIGHT, OBSERVATION, or TENSION — something true about the industry, the problem, or the role that only someone who has thought deeply about it would say
- It should make the reader think "okay, this person gets it" within the first sentence
- It can reference something specific you found in your research — a recent launch, a stated challenge, a market reality
- Length: 2-4 sentences max. Dense. Every word earns its place.

BODY PARAGRAPHS:
- Paragraph 2: Connect the candidate's MOST RELEVANT project or experience directly to the core problem this role solves. Name the project. Be specific about what they built, why, and what it did. Do not summarize their resume — show the thinking behind the work.
- Paragraph 3: Zoom out — show you understand the company's broader context and how the candidate fits into it. This is where company research shines. Reference something real about {company_name}.
- Paragraph 4 (OPTIONAL): Only include if there is a critical skill or dimension not covered yet. Otherwise leave empty.

VALUE BULLETS (3-4 bullets):
- Each bullet is a specific, concrete thing the candidate brings or would do
- NOT vague: "strong communication skills" ❌
- YES specific: "Migrate legacy intake workflow to LLM-assisted triage, reducing processing time" ✅
- Under 15 words each
- Should feel like a preview of day-1 contributions, not a list of personality traits

CLOSING PARAGRAPH:
- Forward-looking and confident — not desperate
- Do NOT say "I look forward to hearing from you" or "Thank you for your consideration"
- Show selectivity — hint that the candidate is choosing this company too, not just hoping to be chosen
- 2-3 sentences max

TONE THROUGHOUT:
- Confident but not arrogant
- Specific but not exhausting to read
- Human — contractions are fine, short sentences are good
- Zero buzzwords: no "leverage", "synergy", "passionate", "dynamic", "results-driven", "hardworking"
- Zero filler: every sentence must add information or make a point

WORD COUNT:
- Total body text (opening + paragraphs + bullets + closing): 380–400 words
- This is the sweet spot: full, substantive, and still fits one page with 0.5" margins
- Do NOT go under 380 — the letter will feel thin. Do NOT go over 400 — it will spill to page 2.
- This fills exactly one page. Do not go under 300 or over 380.
- Count carefully before finalizing.

---

OUTPUT — return this exact JSON and nothing else:

{{
  "hiring_manager_name": "Full name if found, else 'Hiring Manager'",
  "hiring_manager_title": "Their title if found, else ''",
  "company_research_summary": "3-4 sentences on what you found — key facts, recent news, culture signals. This is an internal note shown to the candidate, not included in the letter.",
  "hm_research_summary": "What you found about the hiring manager — background, focus, tone. Internal note only.",
  "jd_key_skills": ["top skill 1", "top skill 2", "top skill 3", "top skill 4"],
  "jd_core_problem": "One sentence: the real problem this role is hired to solve",
  "opening_hook": "The first paragraph. Starts with an insight or tension, not 'I'. Specific to this company and role. 2-4 sentences.",
  "body_paragraphs": [
    "Paragraph 2 — candidate's most relevant work connected to the core problem. Specific, named, real.",
    "Paragraph 3 — broader company context + candidate fit. References something real about {company_name}.",
    ""
  ],
  "value_bullets": [
    "Specific, concrete contribution #1",
    "Specific, concrete contribution #2",
    "Specific, concrete contribution #3",
    "Specific, concrete contribution #4"
  ],
  "closing_paragraph": "2-3 sentences. Confident, forward-looking, slightly selective. No 'look forward to hearing from you'.",
  "sign_off": "Sincerely",
  "word_count": 0
}}

After drafting, count the words in: opening_hook + all body_paragraphs + all value_bullets + closing_paragraph.
Set "word_count" to that number. If it is outside 380-400, revise until it fits, then return the final JSON.
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

    # Robust JSON extraction — find the outermost { } block
    result = None
    start = raw_text.find('{')
    if start != -1:
        depth = 0
        for i, ch in enumerate(raw_text[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        result = json.loads(raw_text[start:i+1])
                    except json.JSONDecodeError:
                        pass
                    break

    if result is None:
        raise ValueError(f"Could not extract valid JSON from Claude response.\n\nRaw:\n{raw_text[:600]}")

    # Log research findings
    if result.get("company_research_summary"):
        console.print(f"[dim]  ✓ Company: {result['company_research_summary'][:100]}...[/dim]")
    if result.get("hm_research_summary") and result["hm_research_summary"].strip():
        console.print(f"[dim]  ✓ Hiring Manager: {result['hm_research_summary'][:100]}...[/dim]")
    if result.get("jd_core_problem"):
        console.print(f"[dim]  ✓ Core problem: {result['jd_core_problem'][:100]}[/dim]")

    # Count and display word count
    body_text = " ".join(filter(None, [
        result.get("opening_hook", ""),
        *result.get("body_paragraphs", []),
        *result.get("value_bullets", []),
        result.get("closing_paragraph", ""),
    ]))
    actual_word_count = len(body_text.split())
    result["word_count"] = actual_word_count

    color = "green" if 380 <= actual_word_count <= 400 else "yellow" if actual_word_count < 380 else "red"
    console.print(f"  [{color}]Word count: {actual_word_count} words[/{color}] [dim](target: 380–400)[/dim]")

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
