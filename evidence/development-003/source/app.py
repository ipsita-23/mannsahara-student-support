"""Run with: uv run streamlit run app.py"""

from pathlib import Path

import streamlit as st

from mannsahara.backend import OllamaBackend, UnavailableBackend
from mannsahara.engine import Chatbot, Session
from mannsahara.policy import MAX_INPUT, Route

st.set_page_config(page_title="MannSahara · Student support", page_icon="assets/icon.svg", layout="centered")
st.markdown(
    """<style>
.block-container {max-width: 850px; padding-top: 2.6rem; padding-bottom: 3rem;}
h1 {letter-spacing: -.045em;} h2 {letter-spacing: -.025em;}
[data-testid="stChatMessage"] {border: 1px solid #D3E2DC; border-radius: 16px; padding: 1.1rem;}
.stButton>button {min-height: 44px;} a {text-underline-offset: 3px;}
</style>""",
    unsafe_allow_html=True,
)

if "chat" not in st.session_state:
    st.session_state.chat = Session()
    st.session_state.accepted = False
    st.session_state.display = []

with st.sidebar:
    st.markdown("### MannSahara")
    st.caption("CSE473 · Group 09 · SIH25092")
    st.markdown("**A little space to talk.**\n\nPractice everyday student support using fictional scenarios.")
    st.divider()
    st.markdown(
        "**Need urgent human help?**\n\nContact local emergency services or the nearest emergency department. "
        "Reach a trusted nearby person or campus staff member."
    )
    st.caption("Location is unknown. No verified regional contacts are configured.")
    st.divider()
    outage = st.toggle(
        "Simulate model outage", help="Demonstrates that fixed crisis responses remain available."
    )
    if st.button("Clear session / start fresh", use_container_width=True):
        st.session_state.chat.clear()
        st.session_state.display = []
        st.session_state.accepted = False
        st.rerun()
    st.caption(
        "Session memory only. Ordinary chats are not saved or exported. This prototype makes no emergency contact."
    )
    with st.expander("Project evidence"):
        st.write("Ipsita Umang · 12309971\n\nAnnamneendi Suresh Kumar · 12317960")
        evidence = sorted(Path("evidence").glob("*/cases.csv"))
        if evidence:
            st.download_button(
                "Download synthetic test log",
                evidence[-1].read_bytes(),
                "mannsahara-synthetic-test-log.csv",
                "text/csv",
            )
        st.caption(
            "Logs contain only the frozen fictional evaluation set. Quality review by both students is pending."
        )

st.caption("STUDENT WELLBEING / SYNTHETIC DEMO")
st.title("You don’t have to figure\nit all out at once.")
st.markdown("MannSahara offers a supportive conversation and one small next step.")
st.info(
    "**AI support prototype, for synthetic scenarios only.** Use invented messages; do not enter real student or "
    "clinical disclosures. This tool cannot diagnose, treat, advise on medication, or provide emergency intervention."
)

if not st.session_state.accepted:
    st.subheader("Before we begin")
    st.write(
        "Try a fictional concern about studies, belonging, or adjusting to campus life. "
        "If a conversation suggests danger, the demo switches to a fixed referral message."
    )
    if st.button("Begin fictional conversation", type="primary"):
        st.session_state.accepted = True
        st.rerun()
    st.stop()

if not st.session_state.display:
    st.markdown("#### What’s on your fictional student’s mind?")
    st.caption("Try: “I feel overwhelmed by next week’s exams.” Or: “I cannot keep going like this.”")

for turn in st.session_state.display:
    with st.chat_message("user"):
        st.text(turn["input"])
    with st.chat_message("assistant"):
        if turn["route"] == Route.ESCALATE:
            st.error("Urgent human support")
        elif turn["route"] == Route.SAFE_FALLBACK:
            st.warning("Limited response · safety check")
        elif turn["route"] == Route.CLARIFY:
            st.info("A quick safety check")
        st.text(turn["response"])
        with st.expander("Demo routing details"):
            st.caption(f"{turn['route']} · {turn['reason']} · {turn['latency_ms']:.0f} ms")

text = st.chat_input("Write a fictional message", max_chars=MAX_INPUT)
if text:
    backend = UnavailableBackend() if outage else OllamaBackend()
    with st.spinner("Preparing a supportive response…"):
        reply = Chatbot(backend).respond(st.session_state.chat, text)
    st.session_state.display.append({"input": text, **reply.record()})
    # Bound display memory as well as model context. Reset is the only way to clear escalation.
    st.session_state.display[:] = st.session_state.display[-20:]
    st.rerun()
