from flask import Flask, render_template, request
from pypdf import PdfReader
import os
import subprocess
import re

app = Flask(__name__)

# ==============================
# CONFIGURATION
# ==============================

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ollama
OLLAMA_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
)

OLLAMA_MODEL = "llama3.2:3b"


# ==============================
# SKILLS DATABASE
# ==============================

SKILLS = [
    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
    "TypeScript",
    "HTML",
    "CSS",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Flask",
    "Django",
    "React",
    "Node.js",
    "Git",
    "GitHub",
    "AWS",
    "Azure",
    "Docker",
    "Linux",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "Data Analysis",
    "Data Visualization",
    "Artificial Intelligence",
    "AI",
    "Power BI",
    "Excel",
    "REST API",
    "API",
    "Bootstrap",
    "Tailwind CSS",
]


# ==============================
# CLEAN AI RESPONSE
# ==============================

def clean_ai_response(text):

    if not text:
        return ""

    # Remove ANSI terminal escape codes
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)

    # Remove Ollama terminal artifacts
    text = text.replace("\x1b", "")
    text = text.replace("[0m", "")
    text = text.replace("[1D", "")
    text = text.replace("[K", "")

    return text.strip()


# ==============================
# LOCAL AI
# ==============================

def get_ai_suggestions(resume_text, job_description):

    prompt = f"""
You are an expert technical recruiter and professional resume reviewer.

Analyze the candidate's resume against the job description.

RESUME:
{resume_text[:12000]}

JOB DESCRIPTION:
{job_description[:12000]}

Give practical suggestions for improving this resume for an entry-level IT/software job.

Use exactly these sections:

1. RESUME STRENGTHS
- Mention the strongest parts of the resume.

2. MISSING OR WEAK SKILLS
- Identify important skills from the job description that are missing or weak.

3. IMPORTANT KEYWORDS
- List useful ATS keywords from the job description.

4. PROFESSIONAL SUMMARY
- Give an improved short professional summary.

5. PROJECT IMPROVEMENTS
- Explain how projects can be written more professionally.

6. TECHNICAL SKILLS
- Suggest technical skills that should be highlighted.

7. ATS OPTIMIZATION
- Give practical ATS improvement tips.

Keep the response concise, professional and useful.
Do not invent qualifications, experience, certifications or projects that are not present in the resume.
"""

    try:

        if not os.path.exists(OLLAMA_PATH):

            return (
                "Ollama was not found.\n\n"
                "Please make sure Ollama is installed on your computer."
            )

        result = subprocess.run(
            [
                OLLAMA_PATH,
                "run",
                OLLAMA_MODEL,
                prompt
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=180
        )

        if result.returncode != 0:

            error_message = result.stderr.strip()

            return (
                "Ollama could not generate suggestions.\n\n"
                f"Error: {error_message}"
            )

        response = clean_ai_response(result.stdout)

        if not response:

            return (
                "The AI did not return a response. "
                "Please try analyzing the resume again."
            )

        return response

    except subprocess.TimeoutExpired:

        return (
            "AI analysis took too long.\n\n"
            "Please try again. Local AI can take some time "
            "when running for the first time."
        )

    except Exception as e:

        return f"AI Error:\n\n{str(e)}"


# ==============================
# HOME PAGE
# ==============================

@app.route("/", methods=["GET", "POST"])
def home():

    skills = []
    missing_skills = []
    match_percentage = None
    ai_suggestions = None
    error = None

    if request.method == "POST":

        try:

            # --------------------------
            # GET FORM DATA
            # --------------------------

            file = request.files.get("resume")

            job_description = request.form.get(
                "job_description",
                ""
            ).strip()

            # --------------------------
            # CHECK PDF
            # --------------------------

            if not file:

                error = "Please upload your resume PDF."

                return render_template(
                    "index.html",
                    skills=skills,
                    missing_skills=missing_skills,
                    match_percentage=match_percentage,
                    ai_suggestions=ai_suggestions,
                    error=error
                )

            if file.filename == "":

                error = "Please select a PDF resume."

                return render_template(
                    "index.html",
                    skills=skills,
                    missing_skills=missing_skills,
                    match_percentage=match_percentage,
                    ai_suggestions=ai_suggestions,
                    error=error
                )

            if not file.filename.lower().endswith(".pdf"):

                error = "Only PDF resumes are supported."

                return render_template(
                    "index.html",
                    skills=skills,
                    missing_skills=missing_skills,
                    match_percentage=match_percentage,
                    ai_suggestions=ai_suggestions,
                    error=error
                )

            # --------------------------
            # CHECK JOB DESCRIPTION
            # --------------------------

            if not job_description:

                error = "Please paste the job description."

                return render_template(
                    "index.html",
                    skills=skills,
                    missing_skills=missing_skills,
                    match_percentage=match_percentage,
                    ai_suggestions=ai_suggestions,
                    error=error
                )

            # --------------------------
            # SAVE PDF
            # --------------------------

            filename = file.filename

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            # --------------------------
            # READ PDF
            # --------------------------

            reader = PdfReader(filepath)

            resume_text = ""

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:

                    resume_text += page_text + "\n"

            # --------------------------
            # CHECK EXTRACTED TEXT
            # --------------------------

            if not resume_text.strip():

                error = (
                    "Could not extract text from this PDF. "
                    "Please upload a text-based PDF resume."
                )

                return render_template(
                    "index.html",
                    skills=skills,
                    missing_skills=missing_skills,
                    match_percentage=match_percentage,
                    ai_suggestions=ai_suggestions,
                    error=error
                )

            # --------------------------
            # LOWERCASE TEXT
            # --------------------------

            resume_lower = resume_text.lower()

            job_lower = job_description.lower()

            # --------------------------
            # FIND RESUME SKILLS
            # --------------------------

            for skill in SKILLS:

                if skill.lower() in resume_lower:

                    skills.append(skill)

            # --------------------------
            # FIND JOB SKILLS
            # --------------------------

            job_skills = []

            for skill in SKILLS:

                if skill.lower() in job_lower:

                    job_skills.append(skill)

            # --------------------------
            # FIND MISSING SKILLS
            # --------------------------

            for skill in job_skills:

                if skill not in skills:

                    missing_skills.append(skill)

            # --------------------------
            # MATCH PERCENTAGE
            # --------------------------

            if job_skills:

                matched_skills = len(job_skills) - len(
                    missing_skills
                )

                match_percentage = round(
                    (matched_skills / len(job_skills)) * 100
                )

            else:

                match_percentage = 0

            # --------------------------
            # AI SUGGESTIONS
            # --------------------------

            ai_suggestions = get_ai_suggestions(
                resume_text,
                job_description
            )

        except Exception as e:

            error = f"Analysis Error: {str(e)}"

    # --------------------------
    # DISPLAY PAGE
    # --------------------------

    return render_template(
        "index.html",
        skills=skills,
        missing_skills=missing_skills,
        match_percentage=match_percentage,
        ai_suggestions=ai_suggestions,
        error=error
    )


# ==============================
# RUN APPLICATION
# ==============================

if __name__ == "__main__":

    print("\n======================================")
    print(" AI RESUME CHECKER PRO")
    print("======================================")
    print("Local AI: Ollama")
    print("Model:", OLLAMA_MODEL)
    print("Website: http://127.0.0.1:5000")
    print("======================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )