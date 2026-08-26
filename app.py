import streamlit as st
import os
import pandas as pd
from core.config import PRESET_TOPICS, DEFAULT_TOPIC, get_api_key
from core.agents import LeoAgent
from core.evaluator import EvaluatorAgent, EvaluationResult

# Page Setup
st.set_page_config(
    page_title="Cognilac - AI Reverse Tutoring",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS Styling
st.markdown("""
<style>
    /* Global Styling */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Header Banner */
    .header-box {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(224, 86, 76, 0.4);
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #E0564C, #F87171);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
        letter-spacing: 1px;
    }
    .role-badge-container {
        display: flex;
        gap: 12px;
        margin-top: 10px;
        margin-bottom: 8px;
        flex-wrap: wrap;
    }
    .role-pill {
        background: rgba(224, 86, 76, 0.15);
        border: 1px solid rgba(224, 86, 76, 0.4);
        color: #F87171;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .quote-banner {
        font-style: italic;
        color: #94A3B8;
        font-size: 0.92rem;
        margin-top: 6px;
    }

    /* Dashboard Cards */
    .mastery-score-box {
        text-align: center;
        background: linear-gradient(135deg, rgba(224, 86, 76, 0.15), rgba(99, 102, 241, 0.15));
        border: 2px solid #E0564C;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .mastery-score-val {
        font-size: 3.4rem;
        font-weight: 900;
        color: #F87171;
        line-height: 1;
    }
    .mastery-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        margin-top: 6px;
    }

    /* Badges */
    .badge-master { background: #10B981; color: #ffffff; }
    .badge-good { background: #06B6D4; color: #ffffff; }
    .badge-needs-simplicity { background: #F59E0B; color: #ffffff; }
    .badge-gaps { background: #EF4444; color: #ffffff; }

    /* Concept Tags */
    .tag-mastered {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid #10B981;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 3px;
    }
    .tag-gap {
        background-color: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid #F59E0B;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 3px;
    }
    .tag-jargon {
        background-color: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid #EF4444;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 3px;
    }

    /* Highlight Box */
    .highlight-box {
        background-color: rgba(30, 41, 59, 0.7);
        border-left: 4px solid #E0564C;
        padding: 12px;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .misconception-card {
        background: rgba(168, 85, 247, 0.1);
        border: 1px solid #A855F7;
        border-radius: 10px;
        padding: 12px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

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

# Sidebar Configuration
with st.sidebar:
    if os.path.exists("assets/cognilac_logo.png"):
        st.image("assets/cognilac_logo.png", use_container_width=True)
    else:
        st.markdown("## 🤖 **COGNILAC**")
    
    st.caption("AI Reverse-Tutoring & Adaptive Socratic Evaluator")
    st.divider()

    # API Key Input
    user_api_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Provided via .env or entered here. Never exposed.",
    )
    api_key = get_api_key(user_api_key)

    if not api_key:
        st.warning("⚠️ No API Key detected. Operating in offline demonstration mode.")

    st.divider()
    st.markdown("### 📚 Select Topic")
    
    selected_topic_preset = st.selectbox(
        "Topic Preset:",
        list(PRESET_TOPICS.keys()) + ["✏️ Custom Topic"],
        index=0,
    )

    if selected_topic_preset == "✏️ Custom Topic":
        topic_name = st.text_input("Enter Custom Topic:", value="Quantum Entanglement")
    else:
        topic_name = PRESET_TOPICS[selected_topic_preset]["title"]

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

    if st.button("🔄 Restart Classroom Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.level = 1
        st.session_state.evaluation = None
        st.session_state.history_scores = []
        st.session_state.mastered_set = set()
        st.session_state.gaps_set = set()
        st.rerun()

# Initialize Agents
leo_agent = LeoAgent(
    topic=st.session_state.current_topic,
    level=st.session_state.level,
    misconception_mode=misconception_mode,
    api_key=api_key,
)

evaluator_agent = EvaluatorAgent(api_key=api_key)

# Starter message initialization
if not st.session_state.messages:
    starter_text = leo_agent.get_starter_message()
    st.session_state.messages.append({"role": "assistant", "content": starter_text})

# Header Banner with Cognilac Logo
col_logo, col_banner_text = st.columns([1, 4])
with col_logo:
    if os.path.exists("assets/cognilac_logo.png"):
        st.image("assets/cognilac_logo.png", use_container_width=True)
with col_banner_text:
    st.markdown(f"""
    <div class="header-box" style="margin-bottom: 0px;">
        <div class="header-title">COGNILAC — Reverse Tutoring Platform</div>
        <div class="role-badge-container">
            <span class="role-pill">🧑‍🏫 YOU = TEACHER</span>
            <span class="role-pill">👦 LEO = 10-YR-OLD STUDENT</span>
            <span class="role-pill">⚙️ HIDDEN COGNILAC EVALUATOR</span>
        </div>
        <div class="quote-banner">
            "Traditional quizzes tell you what you got wrong. Cognilac discovers what you don't actually understand."
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Main 2-Column Layout (65% Chat, 35% Dashboard)
col_chat, col_dash = st.columns([65, 35], gap="large")

# ---------------------------------------------------------
# LEFT COLUMN: Socratic Classroom Chat
# ---------------------------------------------------------
with col_chat:
    st.markdown(f"### 👦 Teaching **{st.session_state.current_topic}** to Leo")

    # Render Chat History
    chat_container = st.container(height=480)
    with chat_container:
        for msg in st.session_state.messages:
            avatar = "👦" if msg["role"] == "assistant" else "🧑‍🏫"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # User Input Field
    if teacher_input := st.chat_input(f"Explain {st.session_state.current_topic} in simple terms to Leo..."):
        # Record Teacher Message
        st.session_state.messages.append({"role": "user", "content": teacher_input})
        
        with chat_container:
            with st.chat_message("user", avatar="🧑‍🏫"):
                st.markdown(teacher_input)

        # Generate Leo Response
        with chat_container:
            with st.chat_message("assistant", avatar="👦"):
                with st.spinner("Leo is thinking..."):
                    leo_reply = leo_agent.respond(teacher_input, st.session_state.messages[:-1])
                    st.markdown(leo_reply)
                    st.session_state.messages.append({"role": "assistant", "content": leo_reply})

        # Run Parallel Independent Evaluator
        with st.spinner("Analyzing pedagogical quality & knowledge gaps..."):
            eval_result = evaluator_agent.evaluate_turn(
                topic=st.session_state.current_topic,
                teacher_explanation=teacher_input,
                conversation_history=st.session_state.messages,
                level=st.session_state.level,
                misconception_active=misconception_mode,
                use_search_grounding=use_grounding,
            )
            st.session_state.evaluation = eval_result
            st.session_state.history_scores.append(eval_result.overall_mastery)

            # Update accumulated mastered concepts and knowledge gaps sets
            for item in eval_result.mastered_concepts:
                st.session_state.mastered_set.add(item)
                if item in st.session_state.gaps_set:
                    st.session_state.gaps_set.remove(item)

            for item in eval_result.knowledge_gaps:
                if item not in st.session_state.mastered_set:
                    st.session_state.gaps_set.add(item)

            # Adaptive Level Update
            if eval_result.level_change != 0:
                new_lvl = max(1, min(5, st.session_state.level + eval_result.level_change))
                st.session_state.level = new_lvl

        st.rerun()

# ---------------------------------------------------------
# RIGHT COLUMN: Cognilac Mastery Dashboard
# ---------------------------------------------------------
with col_dash:
    st.markdown("### 📊 Cognilac Mastery Engine")

    eval_data: EvaluationResult = st.session_state.evaluation

    if eval_data is None:
        st.info("💡 **Ready for your first explanation!** Type your response to Leo on the left. The Cognilac Evaluator will score your simplicity, detect jargon, and map your knowledge gaps in real-time.")
    else:
        # 1. Overall Mastery Score Badge (Deterministically Calculated)
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

        st.markdown(f"""
        <div class="mastery-score-box">
            <div style="font-size: 0.8rem; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px;">Cognilac Mastery Score</div>
            <div class="mastery-score-val">{mastery} <span style="font-size: 1.4rem; color: #64748B;">/ 100</span></div>
            <div class="mastery-badge {badge_class}">{standing}</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Session Progress History Trend
        if len(st.session_state.history_scores) > 1:
            st.markdown("**Session Mastery Progress:**")
            df = pd.DataFrame({
                "Turn": [f"Turn {i+1}" for i in range(len(st.session_state.history_scores))],
                "Mastery Score": st.session_state.history_scores
            })
            st.line_chart(df.set_index("Turn"), height=130)

        # 3. 5 Weighted Metrics
        st.markdown("#### 📈 Metric Breakdown")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"**Factual Accuracy (30%)**")
            st.progress(eval_data.factual_accuracy / 100.0)
            st.caption(f"{eval_data.factual_accuracy}%")

            st.markdown(f"**Conceptual Understanding (25%)**")
            st.progress(eval_data.conceptual_understanding / 100.0)
            st.caption(f"{eval_data.conceptual_understanding}%")

            st.markdown(f"**Causal Reasoning (20%)**")
            st.progress(eval_data.causal_reasoning / 100.0)
            st.caption(f"{eval_data.causal_reasoning}%")

        with col_m2:
            st.markdown(f"**Simplicity (15%)**")
            st.progress(eval_data.simplicity / 100.0)
            st.caption(f"{eval_data.simplicity}%")

            st.markdown(f"**Jargon Independence (10%)**")
            st.progress(eval_data.jargon_independence / 100.0)
            st.caption(f"{eval_data.jargon_independence}%")

        st.divider()

        # 4. Misconception Challenge Card (if applicable)
        if eval_data.misconception_detected or misconception_mode:
            corrected_status = "YES ✓" if eval_data.teacher_corrected_misconception else "NO ❌"
            status_color = "#10B981" if eval_data.teacher_corrected_misconception else "#EF4444"
            st.markdown(f"""
            <div class="misconception-card">
                <div style="font-weight: 700; color: #C084FC;">🧠 Misconception Test Challenge</div>
                <div style="margin-top: 4px; font-size: 0.9rem;">
                    Teacher Identified & Corrected: <strong style="color: {status_color};">{corrected_status}</strong>
                </div>
                <div style="font-size: 0.85rem; color: #D8B4FE; margin-top: 4px;">
                    {eval_data.misconception_feedback}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 5. Evolving Knowledge Gap Map
        st.markdown("#### 🗺️ Cognilac Knowledge Gap Map")
        
        # Mastered concepts
        if st.session_state.mastered_set:
            st.markdown("**Mastered Concepts:**")
            tags_html = "".join([f'<span class="tag-mastered">✓ {c}</span>' for c in st.session_state.mastered_set])
            st.markdown(tags_html, unsafe_allow_html=True)

        # Active Gaps
        if st.session_state.gaps_set:
            st.markdown("**Active Knowledge Gaps:**")
            gaps_html = "".join([f'<span class="tag-gap">⚠ {g}</span>' for g in st.session_state.gaps_set])
            st.markdown(gaps_html, unsafe_allow_html=True)

        # Primary Knowledge Gap Highlight Box
        if eval_data.primary_knowledge_gap:
            st.markdown(f"""
            <div class="highlight-box" style="border-left-color: #F59E0B;">
                <strong style="color: #FBBF24;">🎯 Primary Knowledge Gap:</strong><br/>
                <span style="font-size: 0.9rem; color: #FDE68A;">{eval_data.primary_knowledge_gap}</span>
            </div>
            """, unsafe_allow_html=True)

        # Next Challenge Suggestion
        if eval_data.next_challenge:
            st.markdown(f"""
            <div class="highlight-box" style="border-left-color: #06B6D4;">
                <strong style="color: #38BDF8;">🚀 Recommended Next Challenge:</strong><br/>
                <span style="font-size: 0.9rem; color: #BAE6FD;">"{eval_data.next_challenge}"</span>
            </div>
            """, unsafe_allow_html=True)

        # Jargon Warnings
        if eval_data.jargon_detected:
            st.markdown("#### 🚨 Jargon Warning")
            jargon_html = "".join([f'<span class="tag-jargon">❌ {j}</span>' for j in eval_data.jargon_detected])
            st.markdown(jargon_html, unsafe_allow_html=True)

        # Actionable Feedback
        if eval_data.actionable_feedback:
            st.markdown("#### 💡 Pedagogical Feedback")
            st.info(eval_data.actionable_feedback)
