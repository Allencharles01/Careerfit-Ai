import gradio as gr
import fitz  # PyMuPDF
import os
import requests
import json
import re
from dotenv import load_dotenv

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
load_dotenv()

DEFAULT_AI_ENDPOINT = os.getenv("AI_ENDPOINT", "http://localhost:11434/api/generate")
DEFAULT_MODEL_NAME = os.getenv("AI_MODEL_NAME", "qwen2.5:1.5b")
REQUEST_TIMEOUT = int(os.getenv("AI_TIMEOUT", "600"))
MODERN_VERSION_URL = os.getenv("MODERN_URL", "http://localhost:5173")

# ==========================================
# 📝 SAMPLE DATA
# ==========================================
SAMPLE_JD = """Senior Software Engineer - Full Stack (Python & React)

Role Overview:
We are looking for a Senior Software Engineer to build high-performance web applications and AI-driven workflow engines.

Key Responsibilities:
- Design and implement RESTful APIs using Python (FastAPI / Flask / Django).
- Build modern, interactive frontends using React, TypeScript, and TailwindCSS.
- Integrate local and cloud Large Language Models (LLMs) into production applications.
- Optimize database schemas (PostgreSQL / MongoDB) for low latency.
- Write clean, maintainable, and well-tested code with automated CI/CD pipelines.

Requirements:
- 4+ years of professional experience in Python full-stack software development.
- Strong proficiency with Docker, Git, REST APIs, and Cloud Infrastructure (AWS/GCP).
- Experience with AI application frameworks (LangChain, LlamaIndex, Ollama, Gradio).
- Excellent problem-solving skills and system design experience.
"""

SAMPLE_RESUME = """ALLEN CHARLES
Full Stack & AI Engineer | mailme@allencharles.dev

SUMMARY:
Passionate Software Engineer with 3+ years of experience building responsive web platforms, AI tools, and backend microservices using Python, JavaScript, and modern web tech.

TECHNICAL SKILLS:
- Languages: Python, JavaScript, HTML5, CSS3, SQL
- Frameworks & Libraries: FastAPI, Flask, Gradio, React, Node.js, Express
- AI & ML: Ollama, PyMuPDF, LangChain, Prompt Engineering, Local LLM Integration
- Databases & Tools: PostgreSQL, MongoDB Atlas, Git, Docker, REST APIs, Linux

SELECTED PROJECTS:
- CareerFit AI: Resume compatibility analyzer powered by Ollama and Gradio with automated PDF parsing.
- NovaNectar ERP: Responsive enterprise resource planning dashboard with custom interactive analytics.
- Quiz Maker Platform: Full-stack quiz web app migrated to MongoDB Atlas with secure JWT authentication.

EDUCATION:
B.Tech in Computer Science & Engineering
"""

# ==========================================
# 🎨 CSS DESIGN SYSTEM
# ==========================================
theme_css = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');

:root {
    --bg: #f4efe9;
    --card: #ffffff;
    --card-border: rgba(200,190,175,0.45);
    --input-bg: #f9f7f4;
    --input-border: #ddd5c9;
    --heading: #1a1a2e;
    --body: #3a3a4a;
    --muted: #7a7a8a;
    --teal: #0f766e;
    --teal-h: #0d9488;
    --teal-pale: #e6faf7;
    --teal-b: #a7f3d0;
    --shadow: 0 8px 32px rgba(0,0,0,0.06);
    --shadow-h: 0 12px 40px rgba(15,118,110,0.12);
    --nav-bg: #ffffff;
    --nav-border: rgba(200,190,175,0.4);
}
.dark {
    --bg: #050806;
    --card: #1C241E;
    --card-border: rgba(116,135,120,0.25);
    --input-bg: #0f1410;
    --input-border: rgba(116,135,120,0.3);
    --heading: #e2e8e3;
    --body: #b0bab2;
    --muted: #748778;
    --teal: #748778;
    --teal-h: #8fa393;
    --teal-pale: rgba(116,135,120,0.12);
    --teal-b: rgba(116,135,120,0.35);
    --shadow: 0 8px 32px rgba(0,0,0,0.5);
    --shadow-h: 0 12px 40px rgba(84,99,87,0.25);
    --nav-bg: #1C241E;
    --nav-border: rgba(116,135,120,0.2);
}

*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container, .gradio-container > .main {
    background: var(--bg) !important;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    color: var(--body) !important;
    transition: background .3s, color .3s;
}

/* Nuke Gradio internal wrappers */
.gradio-container .block, .gradio-container .form, .gradio-container .wrap,
.gradio-container .panel, .gradio-container .group, .gradio-container fieldset,
.gradio-container .gap { background: transparent !important; border: none !important; box-shadow: none !important; }

/* ---- NAVBAR ---- */
.gradio-container .navbar-wrap.gradio-group {
    position: relative !important;
    margin-bottom: 24px !important;
    background: var(--nav-bg) !important;
    border: 1px solid var(--nav-border) !important;
    border-radius: 16px !important;
    padding: 14px 24px !important;
    box-shadow: var(--shadow) !important;
    transition: background .3s, border-color .3s;
    display: flex !important;
    flex-direction: column !important;
}
.gradio-container .navbar-wrap .block,
.gradio-container .navbar-wrap .form,
.gradio-container .navbar-wrap .prose,
.gradio-container .navbar-wrap .gap {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}
.navbar {
    display: flex; align-items: center; justify-content: space-between;
    background: transparent !important; border: none !important;
    box-shadow: none !important; padding: 0 !important; margin: 0 !important;
    position: relative !important;
    min-height: 54px;
    width: 100% !important;
}
.nav-brand {
    text-align: left;
    z-index: 2;
}
.nav-brand h2 { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 800; color: var(--heading); margin: 0; letter-spacing: -.02em; transition: color .3s; }
.nav-brand p { font-size: .78rem; font-weight: 600; color: var(--teal); margin: 2px 0 0; letter-spacing: .12em; text-transform: uppercase; transition: color .3s; }
.nav-center {
    position: absolute !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 2;
}
.nav-center a {
    display: inline-block; padding: 10px 20px; border-radius: 10px;
    background: linear-gradient(135deg, var(--teal), var(--teal-h));
    color: #fff !important; font-weight: 700; font-size: .88rem;
    text-decoration: none; transition: transform .2s, box-shadow .2s;
    box-shadow: 0 4px 14px rgba(15,118,110,.25);
    white-space: nowrap;
}
.nav-center a:hover { transform: scale(1.03); box-shadow: 0 6px 20px rgba(15,118,110,.4); }
.nav-right-placeholder {
    display: none !important;
}

/* ---- CARDS ---- */
.card {
    background: var(--card) !important; border: 1px solid var(--card-border) !important;
    border-radius: 18px !important; padding: 22px !important;
    box-shadow: var(--shadow) !important;
    transition: border-color .3s, box-shadow .3s, background .3s;
}
.card:hover { border-color: var(--teal-b) !important; box-shadow: var(--shadow-h) !important; }

.c-hdr { font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 700; color: var(--heading); margin-bottom: 14px; display: flex; align-items: center; gap: 10px; transition: color .3s; }
.badge { background: var(--teal-pale); color: var(--teal); padding: 3px 11px; border-radius: 18px; font-size: .75rem; font-weight: 800; border: 1px solid var(--teal-b); }

/* Resume mode toggle buttons */
.mode-toggle { display: flex; gap: 0; margin-bottom: 14px; }
.mode-toggle button {
    flex: 1; padding: 9px 14px; font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: .85rem; font-weight: 700; cursor: pointer;
    border: 1.5px solid var(--card-border); background: var(--input-bg);
    color: var(--muted); transition: all .2s;
}
.mode-toggle button:first-child { border-radius: 10px 0 0 10px; }
.mode-toggle button:last-child { border-radius: 0 10px 10px 0; border-left: none; }
.mode-toggle button.active { background: var(--teal); color: #fff; border-color: var(--teal); }

/* ---- INPUTS ---- */
.gradio-container textarea, .gradio-container input[type="text"] {
    background: var(--input-bg) !important; border: 1.5px solid var(--input-border) !important;
    border-radius: 12px !important; color: var(--heading) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: .94rem !important;
    padding: 13px 15px !important; transition: border-color .2s, box-shadow .2s, background .3s !important;
}
.gradio-container textarea:focus, .gradio-container input[type="text"]:focus {
    border-color: var(--teal) !important; box-shadow: 0 0 0 3px rgba(15,118,110,.12) !important;
}
.gradio-container textarea::placeholder, .gradio-container input::placeholder { color: var(--muted) !important; opacity: .7 !important; }
.gradio-container label, .gradio-container .label-wrap span { color: var(--heading) !important; font-weight: 600 !important; }

/* ---- FILE UPLOAD ---- */
.gradio-container .upload-button, .gradio-container [data-testid="droparea"],
.gradio-container .drop-area, .gradio-container .file-preview {
    background: var(--input-bg) !important; border: 2px dashed var(--input-border) !important;
    border-radius: 14px !important; color: var(--muted) !important; transition: all .25s !important;
}
.gradio-container .upload-button:hover, .gradio-container [data-testid="droparea"]:hover {
    border-color: var(--teal) !important; background: var(--teal-pale) !important;
}

/* ---- ACTION BUTTONS ---- */
.act-btn {
    background: var(--teal) !important; color: #fff !important;
    font-family: 'Outfit', sans-serif !important; font-size: 1.05rem !important;
    font-weight: 700 !important; border: none !important; border-radius: 28px !important;
    padding: 14px 30px !important; box-shadow: 0 6px 22px rgba(15,118,110,.28) !important;
    transition: all .25s ease !important; cursor: pointer !important; margin-top: 8px !important;
}
.act-btn:hover { background: var(--teal-h) !important; transform: translateY(-2px) !important; box-shadow: 0 10px 30px rgba(15,118,110,.42) !important; }

.sample-btn {
    background: transparent !important; color: var(--teal) !important;
    border: 1.5px solid var(--teal-b) !important; border-radius: 10px !important;
    font-size: .85rem !important; font-weight: 700 !important;
    padding: 7px 16px !important; transition: all .2s !important;
}
.sample-btn:hover { background: var(--teal-pale) !important; }

/* ---- REPORT BOX ---- */
#report-box {
    background: var(--card) !important; border: 1.5px solid var(--card-border) !important;
    border-left: 5px solid var(--teal) !important; border-radius: 18px !important;
    padding: 28px !important; min-height: 320px !important;
    box-shadow: var(--shadow) !important; color: var(--body) !important;
    font-size: 1rem; line-height: 1.7;
    transition: background .3s, border-color .3s, color .3s;
}

/* Layout wrapper */
.page-wrap { max-width: 1120px !important; margin: 0 auto !important; padding: 16px 18px 40px !important; position: relative !important; }

/* ---- THEME TOGGLE BUTTONS ---- */
.theme-row {
    position: absolute !important;
    right: 42px !important;
    top: 57px !important;
    transform: translateY(-50%) !important;
    margin: 0 !important;
    z-index: 100 !important;
    display: flex !important;
    gap: 8px !important;
    width: auto !important;
    flex-wrap: nowrap !important;
}
.theme-row .block, .theme-row fieldset, .theme-row .wrap, .theme-row .form { background: transparent !important; border: none !important; box-shadow: none !important; }
.theme-btn-gr {
    width: 36px !important; height: 36px !important; min-width: 36px !important; max-width: 36px !important;
    border-radius: 50% !important; font-size: 1.1rem !important; padding: 0 !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    border: 2px solid transparent !important; cursor: pointer !important;
    transition: all .2s !important; box-shadow: 0 2px 8px rgba(0,0,0,.08) !important;
}
.theme-btn-gr.light-active, .theme-btn-gr:first-child {
    background: #fbbf24 !important; border-color: #f59e0b !important; color: #fff !important;
}
.theme-btn-gr.light-active:hover, .theme-btn-gr:first-child:hover {
    box-shadow: 0 4px 16px rgba(251,191,36,.4) !important; transform: scale(1.1) !important;
}
.theme-btn-gr:last-child {
    background: #64748b !important; border-color: #475569 !important; color: #fff !important;
}
.theme-btn-gr:last-child:hover {
    box-shadow: 0 4px 16px rgba(100,116,139,.4) !important; transform: scale(1.1) !important;
}

/* ---- RESUME MODE TOGGLE ---- */
.mode-toggle-row { gap: 0 !important; margin-bottom: 14px !important; }
.mode-toggle-row .block, .mode-toggle-row fieldset, .mode-toggle-row .wrap, .mode-toggle-row .form { background: transparent !important; border: none !important; box-shadow: none !important; }
.mode-btn {
    padding: 9px 14px !important; font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: .88rem !important; font-weight: 700 !important; cursor: pointer !important;
    border: 1.5px solid var(--card-border) !important; background: var(--input-bg) !important;
    color: var(--muted) !important; transition: all .2s !important;
}
.mode-btn:first-child { border-radius: 10px 0 0 10px !important; }
.mode-btn:last-child { border-radius: 0 10px 10px 0 !important; border-left: none !important; }
.mode-active, .mode-btn.mode-active {
    background: var(--teal) !important; color: #fff !important; border-color: var(--teal) !important;
}

/* ---- MOBILE RESPONSIVENESS ---- */
@media (max-width: 768px) {
    .gradio-container .navbar-wrap.gradio-group {
        padding: 20px 16px !important;
    }
    .navbar {
        flex-direction: column !important;
        align-items: flex-start !important;
        text-align: left !important;
        gap: 12px !important;
        min-height: auto !important;
        padding: 0 !important;
    }
    .nav-brand {
        text-align: left !important;
    }
    .nav-center {
        position: static !important;
        transform: none !important;
        margin: 12px auto 0 !important;
        width: 100% !important;
        text-align: center !important;
    }
    .theme-row {
        position: absolute !important;
        top: 24px !important;
        right: 16px !important;
        transform: none !important;
        margin: 0 !important;
        z-index: 100 !important;
    }
    .nav-right-placeholder {
        display: none !important;
    }
    .card {
        padding: 16px !important;
    }
}

/* Hide default gradio footer */
footer { display: none !important; }
"""

# ==========================================
# 🧩 CORE FUNCTIONS
# ==========================================

def get_pdf_text(file_obj) -> str:
    if file_obj is None:
        return ""
    text = ""
    try:
        with fitz.open(file_obj.name) as doc:
            if doc.is_encrypted:
                return "⚠️ This PDF is password-protected. Please upload an unencrypted file."
            for page in doc:
                text += page.get_text()
        return text.strip() if text else "⚠️ No readable text found in PDF."
    except Exception as err:
        return f"⚠️ PDF extraction error: {err}"


def query_local_llm_json(prompt: str, system: str = "") -> dict:
    payload = {
        "model": DEFAULT_MODEL_NAME,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_predict": 500,
            "repeat_penalty": 1.1
        }
    }
    try:
        r = requests.post(DEFAULT_AI_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        res_str = r.json().get("response", "{}")
        
        # Strip any stray ```json / ``` code fences
        cleaned = res_str.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as je:
            # Fallback regex extraction of JSON block
            match = re.search(r'\{.*\}', res_str, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError as je2:
                    return {"error": f"Failed to parse extracted JSON block: {str(je2)}. Raw response: {res_str}"}
            return {"error": f"Failed to parse AI response as JSON: {str(je)}. Raw response: {res_str}"}
            
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to Ollama at {DEFAULT_AI_ENDPOINT}. Run 'ollama serve' and ensure model '{DEFAULT_MODEL_NAME}' is pulled."}
    except requests.exceptions.Timeout:
        return {"error": "The AI model request timed out. Please try again or use shorter input text."}
    except Exception as e:
        return {"error": f"Error querying local LLM: {str(e)}"}


def run_analysis(jd_text: str, resume_text: str, resume_pdf) -> str:
    final_resume = resume_text.strip() if resume_text else ""
    if not final_resume and resume_pdf:
        final_resume = get_pdf_text(resume_pdf)
    if not jd_text or not final_resume:
        return "### ⚠️ Missing Information\nProvide both a **Job Description** and a **Resume**."

    system_prompt = """You are a senior technical recruiter with 15 years of experience screening resumes against job descriptions for engineering roles.

Rules you must follow:
- Output ONLY valid JSON matching the exact schema requested.
- No preamble, no closing remarks, no formatting other than valid JSON.
- Never invent a numeric "probability of being hired" — only use the four qualitative tiers: Low, Medium, High, Strong.
- Base the compatibility_score strictly on the real overlap between the resume content and the job description requirements — be realistic.
- recommended_projects must NOT repeat any project already listed in the resume text.
- Every gap listed must have a corresponding recommended_project addressing it.
- Keep list items concise and descriptive (under 20 words each)."""

    user_prompt = f"""Analyze the RESUME against the JOB DESCRIPTION below.
You MUST respond with a single JSON object matching exactly this schema:
{{
  "compatibility_score": integer_between_0_and_100,
  "verdict": "string (1-sentence overview of overall alignment)",
  "strengths": [
    "string (first key strength matching the JD)",
    "string (second key strength matching the JD)",
    "string (third key strength matching the JD)"
  ],
  "gaps": [
    "string (first critical gap/missing requirement from JD)",
    "string (second critical gap/missing requirement from JD)"
  ],
  "recommended_projects": [
    {{
      "name": "string (name of a NEW project the candidate should build)",
      "tech_stack": "string (comma-separated tech stack for this project)",
      "why": "string (explain how it specifically closes the first critical gap)"
    }},
    {{
      "name": "string (name of a second NEW project to build)",
      "tech_stack": "string (comma-separated tech stack)",
      "why": "string (explain how it specifically closes the second critical gap)"
    }}
  ],
  "keywords_to_add": ["string (first missing keyword)", "string (second missing keyword)"],
  "format_tip": "string (one concise formatting/ATS tip)",
  "current_chance_tier": "Low | Medium | High | Strong (select exactly one)",
  "current_chance_reasoning": "string (reasoning for current chance based on resume)",
  "projected_chance_tier": "Low | Medium | High | Strong (select exactly one)",
  "projected_chance_reasoning": "string (reasoning for projected chance after building these projects and closing gaps)"
}}

---
JOB DESCRIPTION:
{jd_text[:2000]}

---
RESUME:
{final_resume[:3000]}

---
Produce ONLY the filled-in JSON object above. Do not output any other text or explanation."""

    res_dict = query_local_llm_json(user_prompt, system=system_prompt)

    if "error" in res_dict:
        return f"### ⚠️ Analysis Failed\n\n{res_dict['error']}"

    try:
        # Clamping compatibility score
        raw_score = res_dict.get("compatibility_score", 0)
        try:
            score = int(raw_score)
        except (ValueError, TypeError):
            score = 0
        score = max(0, min(100, score))

        # Format bullets
        strengths_list = res_dict.get("strengths", [])
        if not isinstance(strengths_list, list):
            strengths_list = [str(strengths_list)]
        strengths_bullets = "\n\n".join([f"🔹 {str(item).strip()}" for item in strengths_list if str(item).strip()])
        if not strengths_bullets:
            strengths_bullets = "🔹 None identified."

        gaps_list = res_dict.get("gaps", [])
        if not isinstance(gaps_list, list):
            gaps_list = [str(gaps_list)]
        gaps_bullets = "\n\n".join([f"🔹 {str(item).strip()}" for item in gaps_list if str(item).strip()])
        if not gaps_bullets:
            gaps_bullets = "🔹 None identified."

        # Format recommended projects
        projects_list = res_dict.get("recommended_projects", [])
        if not isinstance(projects_list, list):
            projects_list = []
        projects_bullets = []
        for p in projects_list:
            if isinstance(p, dict):
                p_name = p.get("name", "New Project").strip()
                p_stack = p.get("tech_stack", "Tech Stack").strip()
                p_why = p.get("why", "Closes gap").strip()
                projects_bullets.append(f"🔹 **{p_name}** ({p_stack}) — {p_why}")
        projects_bullets_str = "\n\n".join(projects_bullets)
        if not projects_bullets_str:
            projects_bullets_str = "🔹 None recommended."

        keywords_list = res_dict.get("keywords_to_add", [])
        if not isinstance(keywords_list, list):
            keywords_list = [str(keywords_list)]
        keywords = ", ".join([str(kw).strip() for kw in keywords_list if str(kw).strip()])
        if not keywords:
            keywords = "None missing."

        current_chance_tier = str(res_dict.get("current_chance_tier", "Low")).strip()
        current_chance_reasoning = str(res_dict.get("current_chance_reasoning", "")).strip()
        projected_chance_tier = str(res_dict.get("projected_chance_tier", "Medium")).strip()
        projected_chance_reasoning = str(res_dict.get("projected_chance_reasoning", "")).strip()

        verdict = res_dict.get("verdict", "").strip()

        # Build final report Markdown string in Python
        report = f"""1. 🚀 **Compatibility Score**: {score}%
🔹 {verdict}

2. 🎯 **Core Strengths & Alignment**:
{strengths_bullets}

3. 💡 **Critical Skill Gaps**:
{gaps_bullets}

4. 🏗️ **Recommended Projects**:
{projects_bullets_str}

5. 🛠️ **ATS Optimization & Resume Fixes**:
🔹 **Keywords to add**: {keywords}
🔹 **Format tip**: {res_dict.get("format_tip", "").strip()}

6. 📈 **Chances**: {current_chance_tier} → after improvements: {projected_chance_tier}
🔹 **Now**: {current_chance_reasoning}
🔹 **After**: {projected_chance_reasoning}"""

        return report

    except Exception as e:
        return (f"### ⚠️ Formatting Error\n\n"
                f"Failed to format the AI response into the report structure.\n\n"
                f"**Error:** {str(e)}\n\n"
                f"**Raw Data Received:**\n```json\n"
                f"{json.dumps(res_dict, indent=2)}\n"
                f"```")



def load_sample():
    return SAMPLE_JD, SAMPLE_RESUME, ""


def show_type_mode():
    return gr.update(visible=True), gr.update(visible=False)


def show_upload_mode():
    return gr.update(visible=False), gr.update(visible=True)


# ==========================================
# 🖥️ LAYOUT
# ==========================================

with gr.Blocks(title="CareerFit AI") as demo:

    with gr.Column(elem_classes=["page-wrap"]):

        # ── NAVBAR with embedded theme toggle ──
        with gr.Group(elem_classes=["navbar-wrap"]):
            gr.HTML(f"""
            <nav class="navbar">
                <div class="nav-brand">
                    <h2>CareerFit AI 🚀</h2>
                    <p>Developed by Allen Charles</p>
                </div>
                <div class="nav-center">
                    <a href="{MODERN_VERSION_URL}" target="_blank">Click here to Access a Modern Version</a>
                </div>
                <div class="nav-right-placeholder"></div>
            </nav>
            """)
            with gr.Row(elem_classes=["theme-row"]):
                light_btn = gr.Button("☀️", elem_classes=["theme-btn-gr", "light-active"], scale=0)
                dark_btn = gr.Button("🌙", elem_classes=["theme-btn-gr"], scale=0)

        # ── BODY: TWO COLUMNS ──
        with gr.Row():

            # LEFT: Job Description
            with gr.Column(scale=1, elem_classes=["card"]):
                gr.HTML("<div class='c-hdr'><span class='badge'>JD</span> Job Description</div>")
                sample_btn = gr.Button("✨ Load Sample JD & Resume", elem_classes=["sample-btn"])
                jd_input = gr.Textbox(lines=16, show_label=False, placeholder="Paste the full job description here…")

            # RIGHT: Resume Input (Toggle: Type / Upload)
            with gr.Column(scale=1, elem_classes=["card"]):
                gr.HTML("<div class='c-hdr'><span class='badge'>RESUME</span> Your Resume</div>")

                # Toggle buttons (Gradio-native)
                with gr.Row(elem_classes=["mode-toggle-row"]):
                    type_btn = gr.Button("✍️ Type Resume", elem_classes=["mode-btn", "mode-active"], scale=1)
                    upload_btn = gr.Button("📄 Upload PDF", elem_classes=["mode-btn"], scale=1)

                # Type mode panel (visible by default)
                type_panel = gr.Column(visible=True)
                with type_panel:
                    res_text = gr.Textbox(lines=14, show_label=False, placeholder="Paste or type your resume content here…")

                # Upload mode panel (hidden by default)
                upload_panel = gr.Column(visible=False)
                with upload_panel:
                    res_file = gr.File(file_types=[".pdf"], label="Upload Resume PDF")
                    gr.HTML("<p style='color:var(--muted);font-size:.85rem;margin-top:6px;'>Supported: PDF files only. Text will be extracted automatically.</p>")

        # ── ANALYZE BUTTON ──
        analyze_btn = gr.Button("⚡ Analyze Resume Compatibility", elem_classes=["act-btn"])

        # ── REPORT OUTPUT ──
        with gr.Column(elem_classes=["card"]):
            gr.HTML("<div class='c-hdr'><span class='badge'>REPORT</span> AI Generated Analysis</div>")
            report_output = gr.Markdown(
                value="### 📊 Your Compatibility Report\n*Click **⚡ Analyze** to generate an AI-powered evaluation of your resume against the job description…*",
                elem_id="report-box"
            )

        # ── WIRING ──
        sample_btn.click(load_sample, inputs=[], outputs=[jd_input, res_text, report_output])
        analyze_btn.click(run_analysis, inputs=[jd_input, res_text, res_file], outputs=report_output)

        # Resume mode toggle wiring
        type_btn.click(show_type_mode, inputs=[], outputs=[type_panel, upload_panel])
        upload_btn.click(show_upload_mode, inputs=[], outputs=[type_panel, upload_panel])

        # Theme toggle wiring via JS
        light_btn.click(fn=None, inputs=[], outputs=[], js="""() => {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
            document.querySelectorAll('.gradio-container').forEach(e => e.classList.remove('dark'));
        }""")
        dark_btn.click(fn=None, inputs=[], outputs=[], js="""() => {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
            document.querySelectorAll('.gradio-container').forEach(e => e.classList.add('dark'));
        }""")


if __name__ == "__main__":
    demo.launch(css=theme_css)
