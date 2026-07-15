import gradio as gr
import fitz  # PyMuPDF
import os
import requests
from dotenv import load_dotenv

# --- Config & Env ---
load_dotenv()

AI_ENDPOINT = os.getenv("AI_ENDPOINT", "http://localhost:11434/api/generate")

# Make sure this matches: ollama list
MODEL_NAME = "qwen2.5:1.5b"

print(f"Using AI Endpoint: {AI_ENDPOINT}")
print(f"Using Model: {MODEL_NAME}")

# --- Interface Styling ---
theme_css = """
.gradio-container { 
    background-color: #0b0f19 !important; 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.header-text { text-align: center; color: #60a5fa; margin-top: 10px; }
.card { 
    background: #161b22 !important; 
    border: 1px solid #30363d !important; 
    border-radius: 8px !important; 
    padding: 15px; 
}
.main-btn { 
    background: #238636 !important; 
    color: white !important; 
    font-weight: bold !important;
}
#output-box { 
    background: #0d1117 !important; 
    border-left: 5px solid #60a5fa !important;
    padding: 15px;
}
"""

# --- Helper Functions ---

def get_pdf_text(file_obj):
    if file_obj is None:
        return ""
    text = ""
    try:
        # Using context manager for safety
        with fitz.open(file_obj.name) as doc:
            if doc.is_encrypted:
                return "⚠️ This PDF is encrypted. Please upload an unprotected version."
            for page in doc:
                text += page.get_text()
        return text.strip() if text else "⚠️ No text found in PDF (is it a scanned image?)"
    except Exception as err:
        return f"PDF extraction failed: {err}"


def query_local_llm(user_prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": user_prompt,
        "stream": False,   # Keep False unless you rewrite for streaming
        "options": {
            "temperature": 0.2,
            "num_predict": 200,
            "num_ctx": 2048,
            "top_p": 0.9
        }
    }

    try:
        r = requests.post(AI_ENDPOINT, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()

        return data.get("response", "Model returned empty response.")

    except requests.exceptions.ConnectionError:
        return "⚠️ Cannot connect to Ollama. Make sure `ollama serve` is running."

    except requests.exceptions.Timeout:
        return "⚠️ AI took too long to respond."

    except Exception as e:
        return f"Unexpected API Error: {str(e)}"


def run_compatibility_check(jd_text, raw_resume_text, resume_pdf):

    final_resume = raw_resume_text.strip()
    if not final_resume and resume_pdf:
        final_resume = get_pdf_text(resume_pdf)

    if not jd_text or not final_resume:
        return "### ⚠️ I need both the Job Description and a Resume."

    full_prompt = f"""
Act as an ATS recruiter.

Analyze the resume against the job description.

Return ONLY:

1. Compatibility Score (%)
2. Missing Skills
3. Resume Improvements
4. ATS Keywords
5. One Project (Name + Tech Stack + Idea)

Be concise.

Job Description:
{jd_text[:1000]}

Resume:
{final_resume[:1500]}
"""

    return query_local_llm(full_prompt)


def handle_job_search(title, comp, loc, resume_file):
    if not title:
        return "Enter at least a job title."

    return f"🔍 Searching for **{title}** roles at **{comp or 'Anywhere'}** in **{loc}**...\n\n(Job API integration coming soon.)"


# --- UI Layout ---

with gr.Blocks(css=theme_css) as demo:

    gr.HTML("<h1 class='header-text'>🚀 CareerFit AI</h1>")
    gr.HTML("<p style='text-align:center; color:#8b949e;'>DEVELOPED BY ALLEN CHARLES</p>")
    with gr.Tabs():

        # TAB 1
        with gr.TabItem("📊 Score My Resume"):
            with gr.Row():
                with gr.Column(elem_classes=["card"]):
                    gr.Markdown("#### 1. Paste Job Description")
                    jd_input = gr.Textbox(lines=10, show_label=False)

                with gr.Column(elem_classes=["card"]):
                    gr.Markdown("#### 2. Provide Resume")
                    res_text = gr.Textbox(lines=4, show_label=False)
                    res_file = gr.File(file_types=[".pdf"])

            analyze_btn = gr.Button("Analyze Match", elem_classes=["main-btn"])
            analysis_output = gr.Markdown(elem_id="output-box")

            analyze_btn.click(
                run_compatibility_check,
                inputs=[jd_input, res_text, res_file],
                outputs=analysis_output
            )

        # TAB 2
        with gr.TabItem("🔍 Find Jobs"):
            with gr.Row(elem_classes=["card"]):
                with gr.Column():
                    s_role = gr.Textbox(label="Role Title")
                    s_loc = gr.Textbox(label="Location", value="Remote")

                with gr.Column():
                    s_comp = gr.Textbox(label="Specific Company")
                    s_file = gr.File(file_types=[".pdf"])

            search_btn = gr.Button("Find Matches", elem_classes=["main-btn"])
            search_output = gr.Markdown(elem_id="output-box")

            search_btn.click(
                handle_job_search,
                inputs=[s_role, s_comp, s_loc, s_file],
                outputs=search_output
            )


if __name__ == "__main__":
    demo.launch()
