
import os

import requests
import streamlit as st

API_URL = os.getenv("PROMPTSHIELD_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="PromptShield",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ PromptShield")
st.caption("Prompt Injection & Data Exfiltration Defense")
st.write(
    "Screen prompts and untrusted content before passing them to an AI system."
)

# Check whether the backend is available.
with st.sidebar:
    st.header("Backend status")
    st.caption(API_URL)

    if st.button("Check API health", use_container_width=True):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            response.raise_for_status()
            health = response.json()

            st.success(f"API status: {health.get('status', 'unknown')}")
            st.write(
                "Classifier model available:",
                health.get("classifier_model_available", False),
            )
        except requests.RequestException as exc:
            st.error(f"Could not connect to the API: {exc}")

st.divider()
st.subheader("Screen content")

source = st.selectbox(
    "Content source",
    ["user", "voice_transcript", "tool_output", "document"],
)

prompt = st.text_area(
    "Enter text to screen",
    height=180,
    placeholder="Enter a normal prompt or a test prompt-injection attempt...",
)

if st.button("🛡️ Scan prompt", type="primary", use_container_width=True):
    if not prompt.strip():
        st.warning("Enter some text before scanning.")
    else:
        payload = {
            "text": prompt,
            "source": source,
        }

        try:
            with st.spinner("Screening content..."):
                response = requests.post(
                    f"{API_URL}/screen",
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
                result = response.json()

            decision = result.get("decision", "unknown")
            risk_score = result.get("risk_score")

            st.subheader("Screening result")

            if decision == "allow":
                st.success("Decision: ALLOW")
            elif decision == "block":
                st.error("Decision: BLOCK")
            elif decision == "sanitize":
                st.warning("Decision: SANITIZE")
            else:
                st.info(f"Decision: {decision.upper()}")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Risk score",
                    f"{risk_score:.3f}"
                    if isinstance(risk_score, (int, float))
                    else "Unavailable",
                )

            with col2:
                st.metric("Detection signals", len(result.get("signals", [])))

            st.write("**Reason:**", result.get("reason", "Not provided"))
            st.write("**Request ID:**", result.get("request_id", "Not provided"))

            signals = result.get("signals", [])
            st.subheader("Detection signals")

            if signals:
                st.dataframe(signals, use_container_width=True)
            else:
                st.info("No rule-based detection signals were returned.")

            st.subheader("Sanitized output")
            sanitized_text = result.get("sanitized_text")

            if sanitized_text is None:
                st.write("No sanitized text was returned.")
            else:
                st.text_area(
                    "Resulting text",
                    value=sanitized_text,
                    height=120,
                    disabled=True,
                    label_visibility="collapsed",
                )

            st.session_state["last_request_id"] = result.get("request_id")

        except requests.RequestException as exc:
            st.error(f"API request failed: {exc}")

st.divider()
st.subheader("Audit lookup")

default_request_id = st.session_state.get("last_request_id", "")
request_id = st.text_input(
    "Request ID",
    value=default_request_id,
    placeholder="Paste a request ID from a screening result",
)

if st.button("Fetch audit record"):
    if not request_id.strip():
        st.warning("Enter a request ID.")
    else:
        try:
            response = requests.get(
                f"{API_URL}/audit/{request_id.strip()}",
                timeout=10,
            )

            if response.status_code == 404:
                st.warning("No audit record was found for this request ID.")
            else:
                response.raise_for_status()
                st.json(response.json())

        except requests.RequestException as exc:
            st.error(f"Audit lookup failed: {exc}")
