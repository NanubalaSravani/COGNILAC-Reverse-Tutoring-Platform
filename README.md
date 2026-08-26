# 🐞 Cognilac — AI Reverse-Tutoring & Socratic Evaluator

**Submission for Hack2skill PromptWars x Diksuchi EdTech**

> "Traditional quizzes tell you what you got wrong. Cognilac discovers what you don't actually understand."

Cognilac flips the classroom. Instead of an AI tutoring a human, **you** become the teacher and explain STEM topics to **Leo**, a curious 10-year-old AI student built on Google Gemini. While you teach, a hidden **Cognilac Evaluator** silently grades your explanation on pedagogical quality, factual accuracy, and clarity — surfacing the gaps in your own understanding in real time.

---

## 🏆 Hackathon Details

| | |
|---|---|
| **Event** | Hack2skill PromptWars x Diksuchi EdTech |
| **Challenge Vertical** | AI Reverse-Tutoring & Adaptive Socratic STEM Learning |
| **Target Persona** | Student/Teacher pair — a human teacher explaining a concept to a 10-year-old AI persona |
| **Core Idea** | Apply the Feynman Technique: you only truly understand something if you can teach it simply to a child. Cognilac operationalizes that as a graded, adaptive learning loop. |

---

## ✨ Why Cognilac

Most learning tools test recall. Cognilac tests **understanding** — the harder, more honest signal. By making the user explain rather than answer, it exposes shaky mental models before an exam or interview does, and it does so through a natural, conversational interface rather than a form or quiz.

---

## 🧠 How It Works

Cognilac runs two AI agents in parallel on every message you send:

### 1. Leo — the Student Agent (`core/agents.py`)
- Roleplays a genuinely curious, naive 10-year-old.
- Asks follow-up questions the way a real child would, not a scripted bot.
- Supports a **Misconception Challenge Mode**, where Leo pushes back with common wrong beliefs to see if you can correct them.
- **Adaptive Difficulty**, Level 1 through 5, that scales Leo's questions to how well you're explaining.

### 2. The Cognilac Evaluator (`core/evaluator.py`)
Runs silently alongside the conversation and scores every explanation across five weighted metrics:

| Metric | Weight |
|---|---|
| Factual Accuracy | 30% |
| Conceptual Understanding | 25% |
| Causal Reasoning | 20% |
| Simplicity | 15% |
| Jargon Independence | 10% |

**Dynamic Hybrid Evaluation:**
- **Online:** uses Gemini's structured JSON output for nuanced, context-aware scoring.
- **Offline:** falls back to algorithmic heuristics (word complexity, causal-connective detection, term matching) — no hardcoded or static scores, even without an internet connection.

---

## 🖥️ Product Walkthrough

Cognilac is organized into three workspaces:

- **💬 Socratic Classroom Workspace** — the live chat where you teach Leo, with a mastery panel alongside it that fills in as you talk.
- **📊 Mastery Engine Analytics** — a dashboard view of your scores across sessions and metrics.
- **📄 Study Source Manager** — manage what Leo already "knows" so your explanations get evaluated against a real source.

**Learning Source options let you choose how a topic is seeded:**
- **Preset Topic** — pick from curated STEM topics (e.g., Cryptography) with built-in starter questions.
- **Custom Topic** — type any topic you want to teach.
- **Upload Study Material** — ground the session in your own notes or textbook content.

**Demo Modes** (toggleable) showcase the platform's range for judges:
- **Misconception Test Challenge** — Leo deliberately raises a common misconception to see if you catch and correct it.
- **Google Search Grounding** — lets Leo's fact-checking pull from live web results.

Other UI touches: a **Light & Clean / Dark Cyberpunk** theme toggle, a **speak-or-upload-audio** input option for verbal explanations, and a one-click **Restart Classroom Session**.

---

## 🔒 Security Features

1. **Secret & Key Protection**
   - Secrets loaded via `.env` with `python-dotenv`.
   - `.env` and other sensitive files excluded from Git (`.gitignore`) and Docker images (`.dockerignore`).
2. **Input Sanitization & Boundary Protection**
   - User inputs and topic parameters are sanitized, stripping null bytes and non-printable control characters.
   - Input length capped at 1,500 characters to guard against prompt injection and token exhaustion.
3. **Session Rate Capping**
   - Chat sessions capped at 30 turns to prevent bot loops and runaway API usage.
4. **Production Server Hardening**
   - Streamlit security options set in `.streamlit/config.toml`: `enableXsrfProtection = true`, `enableCORS = true`, minimal toolbar, disabled usage stats, hidden tracebacks.
5. **XSS Protection**
   - Any dynamic HTML rendered with `unsafe_allow_html=True` is escaped via `html.escape()`.

---

## 🧪 Running Automated Tests

```bash
python -m unittest discover -s tests
```

Coverage includes:
- Topic normalization & preset starter-question lookups — `tests/test_config.py`
- Input sanitization & student agent behavior — `tests/test_agents.py`
- Deterministic mastery calculation & dynamic offline evaluator — `tests/test_evaluator.py`

---

## 🛠 Local Development Quickstart

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Add your Gemini API key to a `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

---

## 🚀 Deployment

### Option 1 — Streamlit Community Cloud (recommended, free)
1. Push the repo to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Cognilac"
   git remote add origin https://github.com/your-username/cognilac.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New App**, then select your repo, branch (`main`), and main file (`app.py`).
4. Under **Advanced settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   ```
5. Click **Deploy!** — Cognilac will be live at an HTTPS URL.

### Option 2 — Google Cloud Run

**Method A — Cloud Console (no CLI):**
1. Push the project to GitHub (`.env` excluded via `.gitignore`).
2. Open the [Cloud Run Console](https://console.cloud.google.com/run) and click **Create Service**.
3. Choose **Continuously deploy from a repository** and connect your GitHub repo.
4. Set Build Type to **Dockerfile**.
5. Set **Container Port** to `8501`.
6. Under **Environment Variables**, add `GEMINI_API_KEY`.
7. Under **Authentication**, choose **Allow unauthenticated invocations** for a public URL.
8. Click **Create** — GCP builds the container and returns your live URL.

**Method B — Cloud Shell:**
1. Open [Google Cloud Shell](https://shell.cloud.google.com).
2. Clone or upload the project.
3. Deploy:
   ```bash
   gcloud run deploy cognilac \
     --source . \
     --region us-central1 \
     --port 8501 \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY="your_actual_api_key_here"
   ```

---

## 🗺 Roadmap Ideas

- Persistent mastery history across multiple topics and sessions.
- Peer-teaching mode: two humans teach Leo the same topic and compare mastery scores.
- Classroom/teacher dashboard for tracking multiple students' explanations over time.

---

##  Acknowledgements

Built for **Hack2skill PromptWars x Diksuchi EdTech**, powered by **Google Gemini** and **Streamlit**.