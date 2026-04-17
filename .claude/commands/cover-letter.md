Generate a personalized, research-backed cover letter as a ready-to-submit .docx file.

## Step 1 — Load or Create Profile

Check if `profile.yaml` exists in the current directory.

**If it does NOT exist**, ask the user these questions one by one and save the answers to `profile.yaml`:

```
Personal Info:
- Full name
- Email address
- Phone number
- LinkedIn URL (default: https://www.linkedin.com/in/arulprashath01/)
- GitHub URL (default: https://github.com/Aroool)
- Portfolio URL (default: https://arulprashath-portfolio.vercel.app/)
- Location (city, state)

Career:
- Target role / type of job you're looking for
- Years of total experience
- Professional headline (1 sentence — how you'd describe yourself)
- What makes you different from other candidates? (be specific)

Education:
- Degree
- School / University
- Graduation year
- GPA (optional)

Skills:
- Technical skills (list them out, be specific e.g. "Python (FastAPI, async)")
- Soft skills / working style (1-2 sentences)

Work Experience (most recent first, repeat for each role):
- Company name
- Job title
- Duration (e.g. Jan 2023 – Present)
- One-line summary
- Key achievements (quantified where possible)

Projects (repeat for each):
- Project name
- URL (if any)
- What it is and what problem it solves
- Impact / result
- Tech stack

Additional:
- Industries you're targeting
- Availability (e.g. immediate, 2 weeks notice)
- Visa / work authorization status (optional)
- Anything else that should inform your cover letters
```

Save all answers to `profile.yaml` in YAML format.

**If it DOES exist**, read `profile.yaml` and ask: "Edit your profile before generating? (y/n)" — default no. If yes, re-run the questions above with current values as defaults.

---

## Step 2 — Collect Job Details

Tell the user:
```
Job Details
Options:
  • Paste a job URL (Greenhouse, Lever, Indeed — public boards)
  • Paste JD text directly (for Handshake, LinkedIn, Workday — login-required sites)
  → Paste the URL or first line of JD, then type DONE on a new line when finished
```

Collect the input. If it's a URL from a login-required platform (handshake.com, linkedin.com/jobs, workday.com, myworkdayjobs.com), tell the user that platform requires login and ask them to paste the JD text instead, ending with DONE.

---

## Step 3 — Auto-Extract Job Metadata

From the JD text, extract:
- Company name
- Role / job title
- Hiring manager name (if explicitly mentioned in the JD)

Show what you found:
```
Detected from JD:
  Company  : [name]
  Role     : [title]
  HM       : [name or "(not found)"]
Press Enter to confirm or type a correction.
```

Let the user confirm or correct each field.

---

## Step 4 — Research

Using web search, research the following. Do all searches before writing a single word of the letter.

**Company research** (2-3 searches):
- What they actually do (real product/service, not PR version)
- Current stage: early startup, scaling, enterprise?
- Recent news: funding, product launches, pivots, expansions, layoffs
- Their tech stack or operational approach if visible
- What kind of people they hire, what they value
- Any pain points, bold bets, or challenges they are known for
- What they are proud of (blog, LinkedIn, press)

**Hiring manager research** (1-2 searches, if name provided):
- LinkedIn profile, articles, talks they've given
- Their background and what they care about professionally
- Their tone and communication style

**JD analysis** (from the text itself, no search needed):
- Top 3-5 non-negotiable skills or experiences required
- The core problem this role is hired to solve (not the job title — the actual problem)
- Any language or phrases the company repeats (signals their values)
- Culture signals in the JD

---

## Step 5 — Generate Cover Letter Content

Write the cover letter body following these rules exactly:

**OPENING HOOK** (most important):
- Must NOT start with: "I", "My name", "I am writing", "I am excited", "I am applying", "I have always"
- Must NOT be a compliment ("Your innovative approach...")
- Start with an INSIGHT, TENSION, or OBSERVATION — something that only someone who has thought deeply about this company/role would say
- Reference something real from your research — a recent launch, a market reality, a stated challenge
- 2-4 sentences. Dense. Every word earns its place.

**BODY PARAGRAPH 2**:
- Connect the candidate's most relevant project or experience directly to the core problem this role solves
- Name the project specifically
- Show the thinking behind the work, not just the outcome
- Be specific: tech used, problem faced, decision made

**BODY PARAGRAPH 3**:
- Show you understand the company's broader context
- Reference something specific from your research about this company
- Connect why the candidate fits into their specific situation

**BODY PARAGRAPH 4** (optional):
- Only if a critical skill or angle isn't covered yet
- Otherwise skip entirely

**VALUE BULLETS** (3-4 bullets):
- Specific, concrete day-1 contributions — NOT personality traits
- ❌ "Strong communication skills"
- ✅ "Build Angular components that surface compliance findings by severity in real time"
- Under 15 words each

**CLOSING**:
- Confident and forward-looking
- Never: "I look forward to hearing from you", "Thank you for your consideration"
- Show you're choosing them too — not just hoping to be chosen
- 2-3 sentences

**BANNED WORDS** (never use): leverage, synergy, passionate, dynamic, results-driven, hardworking, excited, thrilled, innovative

**WORD COUNT**: 380–400 words total across opening + paragraphs + bullets + closing. Count carefully. Revise if outside this range.

---

## Step 6 — Build the .docx

Once the cover letter content is ready, save it as a JSON file at `/tmp/cl_content.json` in this exact format:

```json
{
  "hiring_manager_name": "Full name or Hiring Manager",
  "hiring_manager_title": "Their title or empty string",
  "company_name": "Company name",
  "role_title": "Job title",
  "opening_hook": "First paragraph text",
  "body_paragraphs": [
    "Second paragraph text",
    "Third paragraph text",
    ""
  ],
  "value_bullets": [
    "Bullet 1",
    "Bullet 2",
    "Bullet 3",
    "Bullet 4"
  ],
  "closing_paragraph": "Closing paragraph text",
  "sign_off": "Sincerely"
}
```

Then run:
```bash
python3 writer_cli.py /tmp/cl_content.json
```

This will generate the `.docx` file and print the output path.

Show the user the output path and tell them: "Open, review, and submit. Edit freely — it's a Word doc."
