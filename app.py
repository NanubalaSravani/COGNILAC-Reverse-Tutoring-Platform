import streamlit as st
import os
import html
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from core.config import PRESET_TOPICS, get_api_key, CHALLENGE_VERTICAL
from core.agents import LeoAgent
from core.evaluator import EvaluatorAgent, EvaluationResult
from core.document_processor import (
    extract_text_from_file,
    extract_concepts_and_topic,
    get_relevant_chunks,
    transcribe_audio_bytes,
)

# Page Setup & WAI-ARIA Metadata
st.set_page_config(
    page_title="Cognilac - AI Reverse Tutoring Workspace",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State Variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_topic" not in st.session_state:
    st.session_state.current_topic = "Photosynthesis"
if "level" not in st.session_state:
    st.session_state.level = 1
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None
if "history_scores" not in st.session_state:
    st.session_state.history_scores = []
if "mastered_set" not in st.session_state:
    st.session_state.mastered_set = set()
if "gaps_set" not in st.session_state:
    st.session_state.gaps_set = set()
if "learning_source" not in st.session_state:
    st.session_state.learning_source = "Preset Topic"
if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""
if "doc_topic" not in st.session_state:
    st.session_state.doc_topic = ""
if "doc_concepts" not in st.session_state:
    st.session_state.doc_concepts = []
if "doc_filename" not in st.session_state:
    st.session_state.doc_filename = ""
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "☀️ Light & Clean"

is_dark = (st.session_state.theme_mode == "🌙 Dark Cyberpunk")


def inject_accessibility_and_theme_css(dark_mode: bool) -> None:
    """Inject WAI-ARIA compliant CSS rules with WCAG 2.1 AAA high-contrast standards."""
    if dark_mode:
        css = """
        <style>
            /* DARK MODE (WCAG 2.1 AAA High Contrast) */
            .stApp {
                background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 65%), #0B0F19 !important;
                color: #F8FAFC !important;
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
            }

            /* Keyboard Focus Outlines (Accessibility) */
            *:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible {
                outline: 3px solid #818CF8 !important;
                outline-offset: 2px !important;
            }

            [data-testid="stSidebar"] {
                background: rgba(15, 23, 42, 0.95) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
            }

            [data-testid="stFileUploader"], section[data-testid="stFileUploaderDropzone"] {
                background-color: #1E293B !important;
                border: 2px dashed #475569 !important;
                border-radius: 12px !important;
                color: #F8FAFC !important;
            }
            section[data-testid="stFileUploaderDropzone"] * { color: #F8FAFC !important; }

            [data-testid="stChatInput"] {
                background-color: #1E293B !important;
                border: 1px solid #475569 !important;
                border-radius: 12px !important;
            }
            [data-testid="stChatInput"] textarea { color: #F8FAFC !important; background-color: #1E293B !important; }

            .header-box {
                background: rgba(19, 27, 46, 0.85);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 16px;
                padding: 20px 24px;
                margin-bottom: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            }
            .header-title {
                font-size: 2.2rem;
                font-weight: 900;
                background: linear-gradient(90deg, #818CF8 0%, #38BDF8 50%, #C084FC 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 6px;
            }
            .role-pill {
                background: rgba(99, 102, 241, 0.15) !important;
                border: 1px solid rgba(99, 102, 241, 0.4) !important;
                color: #A5B4FC !important;
                padding: 5px 14px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
            }
            .quote-banner { color: #CBD5E1 !important; font-style: italic; font-size: 0.92rem; margin-top: 8px; }

            .mastery-score-box {
                text-align: center;
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
                border: 1px solid rgba(99, 102, 241, 0.4);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 16px;
            }
            .mastery-score-val {
                font-size: 3.6rem;
                font-weight: 900;
                color: #818CF8 !important;
                line-height: 1;
            }
            .mastery-badge { display: inline-block; padding: 5px 14px; border-radius: 20px; font-weight: 700; font-size: 0.82rem; margin-top: 8px; }
            .badge-master { background: #059669 !important; color: #ffffff !important; }
            .badge-good { background: #0891B2 !important; color: #ffffff !important; }
            .badge-needs-simplicity { background: #D97706 !important; color: #ffffff !important; }
            .badge-gaps { background: #DC2626 !important; color: #ffffff !important; }

            .tag-mastered { background-color: rgba(16, 185, 129, 0.15) !important; color: #34D399 !important; border: 1px solid rgba(16, 185, 129, 0.3) !important; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; display: inline-block; margin: 3px; font-weight: 600; }
            .tag-gap { background-color: rgba(245, 158, 11, 0.15) !important; color: #FBBF24 !important; border: 1px solid rgba(245, 158, 11, 0.3) !important; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; display: inline-block; margin: 3px; font-weight: 600; }
            .tag-jargon { background-color: rgba(239, 68, 68, 0.15) !important; color: #F87171 !important; border: 1px solid rgba(239, 68, 68, 0.3) !important; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; display: inline-block; margin: 3px; font-weight: 600; }

            .highlight-box { background: rgba(19, 27, 46, 0.85) !important; border-left: 4px solid #6366F1 !important; padding: 14px; border-radius: 8px; margin-top: 10px; margin-bottom: 10px; color: #F8FAFC !important; }
            .highlight-box * { color: #F8FAFC !important; }
            .misconception-card { background: rgba(168, 85, 247, 0.15) !important; border: 1px solid rgba(168, 85, 247, 0.4) !important; border-radius: 12px; padding: 14px; margin-top: 10px; color: #F3E8FF !important; }
            .misconception-card * { color: #F3E8FF !important; }
        </style>
        """
    else:
        css = """
        <style>
            /* LIGHT & CLEAN MODE (WCAG 2.1 AAA High Contrast) */
            .stApp {
                background-color: #F8FAFC !important;
                color: #0F172A !important;
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
            }

            /* Keyboard Focus Outlines (Accessibility) */
            *:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible {
                outline: 3px solid #4F46E5 !important;
                outline-offset: 2px !important;
            }

            .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
            [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span,
            [data-testid="stCaptionContainer"], [data-testid="stChatMessage"] p {
                color: #0F172A !important;
                background: transparent !important;
            }

            div[role="radiogroup"] label, div[role="radiogroup"] span, div[role="radiogroup"] p {
                color: #0F172A !important;
                background: transparent !important;
            }

            [data-testid="stSidebar"] {
                background-color: #FFFFFF !important;
                border-right: 1px solid #E2E8F0 !important;
            }
            [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {
                color: #0F172A !important;
            }

            [data-testid="stFileUploader"], section[data-testid="stFileUploaderDropzone"] {
                background-color: #F1F5F9 !important;
                border: 2px dashed #CBD5E1 !important;
                border-radius: 12px !important;
                color: #0F172A !important;
            }
            section[data-testid="stFileUploaderDropzone"] * { color: #0F172A !important; }

            [data-testid="stChatInput"] {
                background-color: #FFFFFF !important;
                border: 1px solid #CBD5E1 !important;
                border-radius: 12px !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
            }
            [data-testid="stChatInput"] textarea { color: #0F172A !important; background-color: #FFFFFF !important; }
            [data-testid="stChatInput"] textarea::placeholder { color: #475569 !important; }

            [data-testid="stChatMessage"] {
                background-color: #FFFFFF !important;
                border: 1px solid #E2E8F0 !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                color: #0F172A !important;
            }

            input, textarea, select, div[data-baseweb="select"] *, div[data-baseweb="popover"] * {
                color: #0F172A !important;
                background-color: #FFFFFF !important;
            }

            button[data-baseweb="tab"] p, button[data-baseweb="tab"] div, button[data-baseweb="tab"] span {
                color: #0F172A !important;
                font-weight: 600 !important;
            }

            .header-box {
                background: linear-gradient(135deg, #FFFFFF 0%, #EEF2FF 100%);
                border: 1px solid #C7D2FE;
                border-radius: 16px;
                padding: 20px 24px;
                margin-bottom: 15px;
                box-shadow: 0 4px 14px rgba(79, 70, 229, 0.08);
            }
            .header-title {
                font-size: 2.2rem;
                font-weight: 900;
                background: linear-gradient(90deg, #4F46E5 0%, #06B6D4 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 6px;
            }
            .role-pill {
                background: #EEF2FF !important;
                border: 1px solid #C7D2FE !important;
                color: #4F46E5 !important;
                padding: 5px 14px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
            }
            .quote-banner { color: #334155 !important; font-style: italic; font-size: 0.92rem; margin-top: 8px; }

            .mastery-score-box {
                text-align: center;
                background: linear-gradient(135deg, #EEF2FF 0%, #E0F2FE 100%);
                border: 2px solid #4F46E5;
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 16px;
            }
            .mastery-score-val { font-size: 3.6rem; font-weight: 900; color: #4F46E5 !important; line-height: 1; }
            .mastery-badge { display: inline-block; padding: 5px 14px; border-radius: 20px; font-weight: 700; font-size: 0.82rem; margin-top: 8px; }
            .badge-master { background: #059669 !important; color: #ffffff !important; }
            .badge-good { background: #0891B2 !important; color: #ffffff !important; }
            .badge-needs-simplicity { background: #D97706 !important; color: #ffffff !important; }
            .badge-gaps { background: #DC2626 !important; color: #ffffff !important; }

            .tag-mastered { background-color: #ECFDF5 !important; color: #047857 !important; border: 1px solid #A7F3D0 !important; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; display: inline-block; margin: 3px; font-weight: 600; }
            .tag-gap { background-color: #FFFBEB !important; color: #B45309 !important; border: 1px solid #FDE68A !important; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; display: inline-block; margin: 3px; font-weight: 600; }
            .tag-jargon { background-color: #FEF2F2 !important; color: #B91C1C !important; border: 1px solid #FCA5A5 !important; padding: 4px 12px; border-radius: 8px; font-size: 0.8rem; display: inline-block; margin: 3px; font-weight: 600; }

            .highlight-box { background-color: #FFFFFF !important; border-left: 4px solid #4F46E5 !important; border-top: 1px solid #E2E8F0 !important; border-right: 1px solid #E2E8F0 !important; border-bottom: 1px solid #E2E8F0 !important; padding: 14px; border-radius: 8px; margin-top: 10px; margin-bottom: 10px; color: #0F172A !important; }
            .highlight-box * { color: #0F172A !important; }

            .misconception-card { background: #F5F3FF !important; border: 1px solid #DDD6FE !important; border-radius: 12px; padding: 14px; margin-top: 10px; color: #4C1D95 !important; }
            .misconception-card * { color: #4C1D95 !important; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


inject_accessibility_and_theme_css(is_dark)

# =========================================================
# SIDEBAR NAVIGATION & CONTROL PANEL
# =========================================================
with st.sidebar:
    st.markdown('<nav aria-label="Control Panel">', unsafe_allow_html=True)
    if os.path.exists("assets/cognilac_logo.png"):
        st.image("assets/cognilac_logo.png", use_container_width=True, caption="Cognilac AI Platform")
    else:
        st.markdown("## 🤖 **COGNILAC**")
    
    st.caption(f"🎯 **Vertical:** {CHALLENGE_VERTICAL}")
    st.caption("● **Status:** ONLINE | EVALUATOR ACTIVE")
    st.divider()

    # Theme Selector
    st.markdown("### 🎨 Interface Theme")
    selected_theme = st.radio(
        "Mode:",
        ["☀️ Light & Clean", "🌙 Dark Cyberpunk"],
        index=0 if not is_dark else 1,
        help="Select WAI-ARIA compliant light or dark visual theme."
    )
    if selected_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = selected_theme
        st.rerun()

    st.divider()
    api_key = get_api_key()

    st.markdown("### 📚 Learning Source")
    learning_source = st.radio(
        "Source Mode:",
        ["Preset Topic", "Custom Topic", "📄 Upload Study Material"],
        index=0 if st.session_state.learning_source == "Preset Topic" else (1 if st.session_state.learning_source == "Custom Topic" else 2),
    )
    st.session_state.learning_source = learning_source

    doc_grounding_context = ""
    active_document_concepts = []

    if learning_source == "Preset Topic":
        selected_topic_preset = st.selectbox(
            "Topic Preset:",
            list(PRESET_TOPICS.keys()),
            index=0,
        )
        topic_name = PRESET_TOPICS[selected_topic_preset]["title"]

    elif learning_source == "Custom Topic":
        topic_name = st.text_input("Enter Custom Topic:", value="Quantum Entanglement")

    else:  # 📄 Upload Study Material
        uploaded_file = st.file_uploader(
            "Upload Study Material",
            type=["pdf", "docx", "txt", "pptx", "csv", "xlsx"],
            help="Upload PDF, DOCX, TXT, PPTX, or CSV/XLSX study notes."
        )
        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            file_name = uploaded_file.name
            if file_name != st.session_state.doc_filename:
                extracted = extract_text_from_file(file_bytes, file_name)
                doc_topic, doc_concepts = extract_concepts_and_topic(extracted, file_name)
                st.session_state.doc_text = extracted
                st.session_state.doc_topic = doc_topic
                st.session_state.doc_concepts = doc_concepts
                st.session_state.doc_filename = file_name
                st.session_state.current_topic = doc_topic
                st.session_state.messages = []
                st.session_state.level = 1
                st.session_state.evaluation = None
                st.session_state.history_scores = []
                st.session_state.mastered_set = set()
                st.session_state.gaps_set = set()
                st.rerun()

        if st.session_state.doc_filename:
            st.success(f"📄 **{st.session_state.doc_filename}**")
            st.caption(f"✓ {len(st.session_state.doc_concepts)} concepts detected")
            
            if st.session_state.doc_concepts:
                st.markdown("**Detected Key Concepts:**")
                concepts_tags = "".join([f'<span class="tag-mastered">✓ {html.escape(c)}</span>' for c in st.session_state.doc_concepts])
                st.markdown(concepts_tags, unsafe_allow_html=True)
            
            topic_name = st.session_state.doc_topic
            active_document_concepts = st.session_state.doc_concepts
        else:
            st.info("👆 Upload a study material file above to begin source-grounded learning!")
            topic_name = "OLAP Operations"

    # Reset button if topic changed
    if topic_name != st.session_state.current_topic:
        st.session_state.current_topic = topic_name
        st.session_state.messages = []
        st.session_state.level = 1
        st.session_state.evaluation = None
        st.session_state.history_scores = []
        st.session_state.mastered_set = set()
        st.session_state.gaps_set = set()
        st.rerun()

    st.divider()
    st.markdown("### ⚙️ Demo Modes")

    misconception_mode = st.toggle(
        "🧠 Misconception Test Challenge",
        value=False,
        help="When enabled, Leo presents a plausible 10-year-old misconception. The evaluator checks if you catch and correct it!",
    )

    use_grounding = st.toggle(
        "🌐 Google Search Grounding",
        value=False,
        help="Enables Google Search Grounding tool for evaluation fact-checking.",
    )

    st.markdown(f"**Adaptive Difficulty:** `Level {st.session_state.level} / 5`")
    st.progress(st.session_state.level / 5.0)

    if st.button("🔄 Restart Classroom Session", use_container_width=True, help="Reset teaching history"):
        st.session_state.messages = []
        st.session_state.level = 1
        st.session_state.evaluation = None
        st.session_state.history_scores = []
        st.session_state.mastered_set = set()
        st.session_state.gaps_set = set()
        st.rerun()
    st.markdown('</nav>', unsafe_allow_html=True)

# Determine turn grounding snippet if document uploaded
if learning_source == "📄 Upload Study Material" and st.session_state.doc_text:
    last_user_msg = ""
    for m in reversed(st.session_state.messages):
        if m["role"] == "user":
            last_user_msg = m["content"]
            break
    doc_grounding_context = get_relevant_chunks(st.session_state.doc_text, query=last_user_msg or st.session_state.current_topic)
    active_document_concepts = st.session_state.doc_concepts

# Initialize Agents
leo_agent = LeoAgent(
    topic=st.session_state.current_topic,
    level=st.session_state.level,
    misconception_mode=misconception_mode,
    api_key=api_key,
    grounding_context=doc_grounding_context,
    document_concepts=active_document_concepts,
)

evaluator_agent = EvaluatorAgent(api_key=api_key)

# Starter message initialization
if not st.session_state.messages:
    starter_text = leo_agent.get_starter_message()
    st.session_state.messages.append({"role": "assistant", "content": starter_text})


# Hero Header Banner
st.markdown('<header role="banner">', unsafe_allow_html=True)
col_logo, col_banner_text = st.columns([1, 4])
with col_logo:
    if os.path.exists("assets/cognilac_logo.png"):
        st.image("assets/cognilac_logo.png", use_container_width=True)
with col_banner_text:
    st.markdown(f"""
    <div class="header-box" style="margin-bottom: 0px;">
        <h1 class="header-title" style="margin:0; font-size:2.2rem;">COGNILAC — Reverse Tutoring Platform</h1>
        <div class="role-badge-container" style="margin-top:8px;">
            <span class="role-pill">🧑‍🏫 YOU = TEACHER</span>
            <span class="role-pill">👦 LEO = 10-YR-OLD STUDENT</span>
            <span class="role-pill">⚙️ SOCRATIC EVALUATOR ENGINE</span>
        </div>
        <div class="quote-banner">
            "Traditional quizzes tell you what you got wrong. Cognilac discovers what you don't actually understand."
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</header>', unsafe_allow_html=True)

if learning_source == "📄 Upload Study Material" and st.session_state.doc_filename:
    concepts_badge_html = "".join([f'<span class="tag-mastered" style="font-size:0.75rem;">✓ {html.escape(c)}</span>' for c in st.session_state.doc_concepts[:6]])
    source_card_bg = "rgba(6, 182, 212, 0.15)" if is_dark else "#ECFEFF"
    source_card_txt = "#38BDF8" if is_dark else "#0891B2"
    st.markdown(f"""
    <div class="highlight-box" style="border-left-color: #06B6D4; background: {source_card_bg}; margin-bottom: 15px;">
        <strong style="color: {source_card_txt}; font-size: 0.95rem;">📖 SOURCE-GROUNDED SESSION ACTIVE</strong><br/>
        <div style="font-size: 0.85rem; margin-top: 4px;">
            <strong>Topic:</strong> {html.escape(st.session_state.doc_topic)} &nbsp;|&nbsp; 
            <strong>Source File:</strong> <code>{html.escape(st.session_state.doc_filename)}</code>
        </div>
        <div style="margin-top: 6px;">
            {concepts_badge_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TABBED WORKSPACE LAYOUT
# ---------------------------------------------------------
tab_classroom, tab_analytics, tab_source = st.tabs([
    "💬 Socratic Classroom Workspace",
    "📊 Mastery Engine Analytics",
    "📄 Study Source Manager",
])

eval_data: Optional[EvaluationResult] = st.session_state.evaluation

# =========================================================
# TAB 1: Socratic Classroom Workspace
# =========================================================
with tab_classroom:
    col_chat, col_dash = st.columns([60, 40], gap="large")

    with col_chat:
        st.markdown(f"### 👦 Teaching **{st.session_state.current_topic}** to Leo")

        # Chat History Container
        chat_container = st.container(height=420)
        with chat_container:
            for msg in st.session_state.messages:
                avatar = "👦" if msg["role"] == "assistant" else "🧑‍🏫"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

        # Check session turn limits
        MAX_SESSION_TURNS = 30
        turn_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        if turn_count >= MAX_SESSION_TURNS:
            st.warning("⚠️ Session turn limit reached (30 turns). Click 'Restart Classroom Session' in the sidebar to begin a fresh teaching session!")
        else:
            # Voice Explanation Input Box
            with st.expander("🎙️ Speak or Upload Audio Explanation", expanded=False):
                col_v1, col_v2 = st.columns([60, 40])
                voice_audio = None
                with col_v1:
                    if hasattr(st, "audio_input"):
                        voice_audio = st.audio_input("Record Spoken Explanation")
                with col_v2:
                    voice_file = st.file_uploader(
                        "Upload Voice Note",
                        type=["wav", "mp3", "m4a", "ogg", "webm"],
                        key="voice_uploader_key"
                    )

                audio_data = voice_audio or voice_file
                if audio_data is not None:
                    audio_bytes = audio_data.getvalue()
                    audio_filename = getattr(audio_data, "name", "voice_explanation.wav")
                    with st.spinner("🎙️ Transcribing audio explanation..."):
                        transcribed_text = transcribe_audio_bytes(audio_bytes, audio_filename, api_key=api_key)
                        if transcribed_text and len(transcribed_text.strip()) >= 3:
                            st.info(f"🎙️ **Transcribed Voice Note:** \"{transcribed_text}\"")
                            if st.button("🚀 Send Voice Explanation to Leo", type="primary", use_container_width=True):
                                clean_voice = f"🎙️ [Voice Note]: {transcribed_text.strip()}"
                                st.session_state.messages.append({"role": "user", "content": clean_voice})
                                with chat_container:
                                    with st.chat_message("user", avatar="🧑‍🏫"):
                                        st.markdown(clean_voice)

                                # Generate Leo Response
                                with chat_container:
                                    with st.chat_message("assistant", avatar="👦"):
                                        with st.spinner("Leo is thinking..."):
                                            leo_reply = leo_agent.respond(clean_voice, st.session_state.messages[:-1])
                                            st.markdown(leo_reply)
                                            st.session_state.messages.append({"role": "assistant", "content": leo_reply})

                                # Run Parallel Independent Evaluator
                                with st.spinner("Analyzing pedagogical quality & knowledge gaps..."):
                                    eval_result = evaluator_agent.evaluate_turn(
                                        topic=st.session_state.current_topic,
                                        teacher_explanation=transcribed_text.strip(),
                                        conversation_history=st.session_state.messages,
                                        level=st.session_state.level,
                                        misconception_active=misconception_mode,
                                        use_search_grounding=use_grounding,
                                        grounding_context=doc_grounding_context,
                                        document_concepts=active_document_concepts,
                                    )
                                    st.session_state.evaluation = eval_result
                                    st.session_state.history_scores.append(eval_result.overall_mastery)

                                    for item in eval_result.mastered_concepts:
                                        st.session_state.mastered_set.add(item)
                                        if item in st.session_state.gaps_set:
                                            st.session_state.gaps_set.remove(item)

                                    for item in eval_result.knowledge_gaps:
                                        if item not in st.session_state.mastered_set:
                                            st.session_state.gaps_set.add(item)

                                    if eval_result.level_change != 0:
                                        new_lvl = max(1, min(5, st.session_state.level + eval_result.level_change))
                                        st.session_state.level = new_lvl

                                st.rerun()

            # User Typed Input Field
            if teacher_input := st.chat_input(f"Explain {st.session_state.current_topic} in simple terms to Leo..."):
                clean_input = teacher_input.strip()
                if len(clean_input) < 3:
                    st.toast("⚠️ Please enter a complete explanation (at least 3 characters).", icon="ℹ️")
                else:
                    st.session_state.messages.append({"role": "user", "content": clean_input})
                    
                    with chat_container:
                        with st.chat_message("user", avatar="🧑‍🏫"):
                            st.markdown(clean_input)

                    with chat_container:
                        with st.chat_message("assistant", avatar="👦"):
                            with st.spinner("Leo is thinking..."):
                                leo_reply = leo_agent.respond(clean_input, st.session_state.messages[:-1])
                                st.markdown(leo_reply)
                                st.session_state.messages.append({"role": "assistant", "content": leo_reply})

                    with st.spinner("Analyzing pedagogical quality & knowledge gaps..."):
                        eval_result = evaluator_agent.evaluate_turn(
                            topic=st.session_state.current_topic,
                            teacher_explanation=clean_input,
                            conversation_history=st.session_state.messages,
                            level=st.session_state.level,
                            misconception_active=misconception_mode,
                            use_search_grounding=use_grounding,
                            grounding_context=doc_grounding_context,
                            document_concepts=active_document_concepts,
                        )
                        st.session_state.evaluation = eval_result
                        st.session_state.history_scores.append(eval_result.overall_mastery)

                        for item in eval_result.mastered_concepts:
                            st.session_state.mastered_set.add(item)
                            if item in st.session_state.gaps_set:
                                st.session_state.gaps_set.remove(item)

                        for item in eval_result.knowledge_gaps:
                            if item not in st.session_state.mastered_set:
                                st.session_state.gaps_set.add(item)

                        if eval_result.level_change != 0:
                            new_lvl = max(1, min(5, st.session_state.level + eval_result.level_change))
                            st.session_state.level = new_lvl

                    st.rerun()

    # RIGHT COLUMN: Real-Time Mastery Engine
    with col_dash:
        st.markdown("### 📊 Live Mastery Engine")

        if eval_data is None:
            st.info("💡 **Ready for your first explanation!** Type or speak your response to Leo on the left. The Cognilac Evaluator will score your simplicity, detect jargon, and map your knowledge gaps in real-time.")
        else:
            mastery = eval_data.overall_mastery
            if mastery >= 88:
                badge_class = "badge-master"
                standing = "🌟 MASTER COGNILAC TEACHER"
            elif mastery >= 75:
                badge_class = "badge-good"
                standing = "🌱 GOOD UNDERSTANDING"
            elif mastery >= 60:
                badge_class = "badge-needs-simplicity"
                standing = "⚠️ NEEDS SIMPLIFICATION"
            else:
                badge_class = "badge-gaps"
                standing = "🧩 HIGH COMPLEXITY / GAPS"

            sub_score_col = "#94A3B8" if is_dark else "#475569"
            st.markdown(f"""
            <div class="mastery-score-box" role="region" aria-label="Mastery Score Panel">
                <div style="font-size: 0.8rem; color: {sub_score_col}; text-transform: uppercase; letter-spacing: 1px;">Cognilac Mastery Score</div>
                <div class="mastery-score-val" aria-live="polite">{mastery} <span style="font-size: 1.4rem; color: #64748B;">/ 100</span></div>
                <div class="mastery-badge {badge_class}">{standing}</div>
            </div>
            """, unsafe_allow_html=True)

            # 5 Weighted Metrics
            st.markdown("#### 📈 Metric Breakdown")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("**Factual Accuracy (30%)**")
                st.progress(eval_data.factual_accuracy / 100.0)
                st.caption(f"{eval_data.factual_accuracy}%")

                st.markdown("**Conceptual Understanding (25%)**")
                st.progress(eval_data.conceptual_understanding / 100.0)
                st.caption(f"{eval_data.conceptual_understanding}%")

                st.markdown("**Causal Reasoning (20%)**")
                st.progress(eval_data.causal_reasoning / 100.0)
                st.caption(f"{eval_data.causal_reasoning}%")

            with col_m2:
                st.markdown("**Simplicity (15%)**")
                st.progress(eval_data.simplicity / 100.0)
                st.caption(f"{eval_data.simplicity}%")

                st.markdown("**Jargon Independence (10%)**")
                st.progress(eval_data.jargon_independence / 100.0)
                st.caption(f"{eval_data.jargon_independence}%")

            if eval_data.primary_knowledge_gap:
                clean_pkg = html.escape(str(eval_data.primary_knowledge_gap))
                pkg_bg = "rgba(245, 158, 11, 0.15)" if is_dark else "#FFFBEB"
                pkg_txt = "#FBBF24" if is_dark else "#B45309"
                st.markdown(f"""
                <div class="highlight-box" style="border-left-color: #F59E0B; background: {pkg_bg};">
                    <strong style="color: {pkg_txt};">🎯 Primary Knowledge Gap:</strong><br/>
                    <span style="font-size: 0.9rem;">{clean_pkg}</span>
                </div>
                """, unsafe_allow_html=True)

            if eval_data.next_challenge:
                clean_nc = html.escape(str(eval_data.next_challenge))
                nc_bg = "rgba(99, 102, 241, 0.15)" if is_dark else "#EEF2FF"
                nc_txt = "#818CF8" if is_dark else "#4338CA"
                st.markdown(f"""
                <div class="highlight-box" style="border-left-color: #6366F1; background: {nc_bg};">
                    <strong style="color: {nc_txt};">🚀 Recommended Next Challenge:</strong><br/>
                    <span style="font-size: 0.9rem;">"{clean_nc}"</span>
                </div>
                """, unsafe_allow_html=True)


# =========================================================
# TAB 2: Mastery Engine Analytics
# =========================================================
with tab_analytics:
    st.markdown("### 📊 Session Mastery Progress & Diagnostic Analytics")

    col_a1, col_a2 = st.columns([50, 50], gap="large")

    with col_a1:
        st.markdown("#### 📈 Mastery Score Trend")
        if len(st.session_state.history_scores) > 0:
            df = pd.DataFrame({
                "Turn": [f"Turn {i+1}" for i in range(len(st.session_state.history_scores))],
                "Mastery Score": st.session_state.history_scores
            })
            st.line_chart(df.set_index("Turn"), height=240)
        else:
            st.info("No teaching turns recorded yet. Explain a concept in the Workspace tab to start tracking progress!")

        if eval_data and eval_data.jargon_detected:
            st.markdown("#### 🚨 Technical Jargon Detected")
            jargon_html = "".join([f'<span class="tag-jargon">❌ {html.escape(str(j))}</span>' for j in eval_data.jargon_detected])
            st.markdown(jargon_html, unsafe_allow_html=True)

    with col_a2:
        st.markdown("#### 🗺️ Knowledge Competency Breakdown")
        if st.session_state.mastered_set:
            st.markdown("**✓ Mastered Concepts:**")
            tags_html = "".join([f'<span class="tag-mastered">✓ {html.escape(str(c))}</span>' for c in st.session_state.mastered_set])
            st.markdown(tags_html, unsafe_allow_html=True)

        if st.session_state.gaps_set:
            st.markdown("**⚠️ Active Knowledge Gaps:**")
            gaps_html = "".join([f'<span class="tag-gap">⚠ {html.escape(str(g))}</span>' for g in st.session_state.gaps_set])
            st.markdown(gaps_html, unsafe_allow_html=True)

        if eval_data and eval_data.actionable_feedback:
            st.markdown("#### 💡 Pedagogical Feedback")
            st.info(eval_data.actionable_feedback)

    # Session Report Export Option
    st.divider()
    if st.session_state.history_scores:
        report_md = f"# Cognilac Socratic Session Report - {st.session_state.current_topic}\n\n"
        report_md += f"- **Topic:** {st.session_state.current_topic}\n"
        report_md += f"- **Latest Mastery Score:** {st.session_state.history_scores[-1]}/100\n"
        report_md += f"- **Mastered Concepts:** {', '.join(st.session_state.mastered_set) or 'None yet'}\n"
        report_md += f"- **Active Gaps:** {', '.join(st.session_state.gaps_set) or 'None'}\n"
        st.download_button(
            "📥 Download Session Mastery Report (Markdown)",
            data=report_md,
            file_name=f"Cognilac_Report_{st.session_state.current_topic}.md",
            mime="text/markdown",
            use_container_width=True,
        )


# =========================================================
# TAB 3: Study Source Manager
# =========================================================
with tab_source:
    st.markdown("### 📄 Study Material & Source Grounding Manager")

    if learning_source == "📄 Upload Study Material" and st.session_state.doc_filename:
        col_s1, col_s2 = st.columns([40, 60], gap="large")

        with col_s1:
            st.markdown("#### ℹ️ Document Metadata")
            st.markdown(f"**Filename:** `{html.escape(st.session_state.doc_filename)}`")
            st.markdown(f"**Extracted Topic:** `{html.escape(st.session_state.doc_topic)}`")
            st.markdown(f"**Total Characters:** `{len(st.session_state.doc_text):,}` chars")
            st.markdown(f"**Detected Concepts:** `{len(st.session_state.doc_concepts)}` concepts")

            st.markdown("#### 🏷️ Detected Concepts List")
            if st.session_state.doc_concepts:
                concepts_tags = "".join([f'<span class="tag-mastered">✓ {html.escape(c)}</span>' for c in st.session_state.doc_concepts])
                st.markdown(concepts_tags, unsafe_allow_html=True)

        with col_s2:
            st.markdown("#### 📖 Active RAG Grounding Excerpt")
            if doc_grounding_context:
                st.code(doc_grounding_context, language="markdown")
            else:
                st.info("Grounding excerpt will display when you explain a concept in the Workspace tab.")

            with st.expander("🔍 View Complete Extracted Text", expanded=False):
                st.text_area("Full Document Content:", value=st.session_state.doc_text, height=300)

    else:
        st.info("ℹ️ You are currently in **Preset / Custom Topic** mode. To use Source-Grounded Learning, select **📄 Upload Study Material** in the sidebar and upload a PDF, DOCX, TXT, PPTX, or CSV/XLSX file.")
