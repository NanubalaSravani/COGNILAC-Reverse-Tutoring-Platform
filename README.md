# 🤖 COGNILAC — AI Reverse Tutoring & Socratic Evaluator

Cognilac is an AI-powered reverse-tutoring platform built with Streamlit and Google Gemini. In Cognilac, the user acts as the **Teacher**, explaining complex STEM topics to **Leo** (a curious 10-year-old AI student). In parallel, the hidden **Cognilac Evaluator** assesses pedagogical quality, simplicity, factual accuracy, and detects knowledge gaps in real-time.

---

## 🎯 Hackathon Challenge Alignment

- **Challenge Vertical**: AI Reverse-Tutoring & Adaptive Socratic STEM Learning
- **Target Persona**: Student / Teacher Pair (Human Teacher explaining to a 10-year-old AI persona)
- **Pedagogical Rationale**: "Traditional quizzes test what you remember. Cognilac discovers what you don't actually understand by turning the user into the teacher (Feynman Technique)."

### Core Architecture & Logic:
1. **Dual Parallel Agents**:
   - **Leo Agent** (`core/agents.py`): Mimics a naive 10-year-old student with misconception challenge modes and adaptive difficulty levels (Level 1–5).
   - **Cognilac Evaluator** (`core/evaluator.py`): Runs asynchronously in parallel to score 5 weighted pedagogical metrics (Factual Accuracy 30%, Conceptual Understanding 25%, Causal Reasoning 20%, Simplicity 15%, Jargon Independence 10%).
2. **Dynamic Hybrid Evaluation**:
   - Uses Gemini LLM structured JSON output when online.
   - Uses algorithmic heuristic analysis (word complexity, causal connectives, term matching) when offline without hardcoded static scores.

---

## 🔒 Security Features Implemented

1. **Secret & Key Protection**:
   - Secrets are loaded via `.env` using `python-dotenv`.
   - `.env` and sensitive files are excluded from Git via `.gitignore` and from Docker images via `.dockerignore`.
2. **Input Sanitization & Boundary Protections**:
   - User inputs and topic parameters are sanitized (stripping null bytes / non-printable control characters).
   - Input lengths are capped (1,500 characters max) to protect against prompt injection and token exhaustion.
3. **Session Rate Capping**:
   - Chat sessions are capped at 30 turns to prevent bot loops and excessive API consumption.
4. **Production Server Hardening**:
   - Configured Streamlit security options in `.streamlit/config.toml` (`enableXsrfProtection = true`, `enableCORS = true`, minimal toolbar, disabled usage stats, hidden tracebacks).
5. **XSS Protection**:
   - Dynamic HTML elements rendered with `unsafe_allow_html=True` are escaped via `html.escape()`.

---

## 🧪 Running Automated Tests

Run the full automated test suite (compatible with `unittest` and `pytest`):

```bash
python -m unittest discover -s tests
```

Tests cover:
- Topic normalization & preset starter question lookups (`tests/test_config.py`)
- Input sanitization & student agent behavior (`tests/test_agents.py`)
- Deterministic mastery calculation & dynamic offline evaluator (`tests/test_evaluator.py`)

---

## 🚀 How to Publish & Deploy

### Option 1: Streamlit Community Cloud (Recommended & Free)
1. Push this repository to **GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Cognilac"
   git remote add origin https://github.com/your-username/cognilac.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
3. Click **New App**, select your repository, branch (`main`), and main file path (`app.py`).
4. Click **Advanced settings...** and add your secret under **Secrets**:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   ```
5. Click **Deploy!** Your app will be live with an HTTPS URL.

---

### Option 2: Deploy to Google Cloud Run

#### Method A: Via Google Cloud Console (No CLI needed)
1. Push your project to GitHub (ensure `.env` is ignored by `.gitignore`).
2. Go to the [Google Cloud Run Console](https://console.cloud.google.com/run).
3. Click **Create Service**.
4. Select **Continuously deploy from a repository** and connect your GitHub repository.
5. Select **Dockerfile** as the Build Type.
6. Under **Container Port**, enter `8501`.
7. Under **Environment Variables**, add:
   - `GEMINI_API_KEY` = `your_gemini_api_key_here`
8. Under **Authentication**, select **Allow unauthenticated invocations** for a public URL.
9. Click **Create**. GCP will build the Docker container and output your live HTTPS web URL!

#### Method B: Via Google Cloud Shell (Cloud Console Terminal)
1. Open [Google Cloud Shell](https://shell.cloud.google.com).
2. Clone or upload your project code into Cloud Shell.
3. Run the deployment command:
   ```bash
   gcloud run deploy cognilac \
     --source . \
     --region us-central1 \
     --port 8501 \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY="your_actual_api_key_here"
   ```

---

## 🛠 Local Development Quickstart

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure your `.env` file contains your Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. Run Streamlit app:
   ```bash
   streamlit run app.py
   ```
