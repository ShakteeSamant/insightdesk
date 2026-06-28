"""Streamlit front-end for InsightDesk.

A lightweight UI that talks to the InsightDesk FastAPI backend. It lets a user:
- check backend health,
- (re)ingest the knowledge base,
- ask a support question and read the grounded answer with citations,
- inspect any ingested document by id.

Run the FastAPI backend first (``uvicorn app.main:app --reload``), then start
this UI with ``streamlit run streamlit_app.py``.
"""
from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

DEFAULT_API_BASE = os.getenv("INSIGHTDESK_API_BASE", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.getenv("INSIGHTDESK_TIMEOUT", "60"))


# --------------------------------------------------------------------------- #
# API helpers
# --------------------------------------------------------------------------- #
def _api(path: str) -> str:
    return f"{st.session_state.api_base.rstrip('/')}{path}"


def check_health() -> tuple[bool, str]:
    """Return (is_healthy, detail) for the backend ``/health`` endpoint."""
    try:
        resp = requests.get(_api("/health"), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("status") == "ok", "online"
    except requests.RequestException as exc:
        return False, str(exc)


def ingest() -> dict[str, Any]:
    resp = requests.post(_api("/ingest"), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def process_query(query: str, user_id: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"query": query}
    if user_id:
        payload["user_id"] = user_id
    resp = requests.post(_api("/process"), json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_doc(doc_id: str) -> dict[str, Any] | None:
    resp = requests.get(_api(f"/docs/{doc_id}"), timeout=REQUEST_TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_answer(result: dict[str, Any]) -> None:
    response = result.get("response", {})
    escalated = response.get("escalate", False)

    if escalated:
        st.warning("This case was **escalated** for human review.", icon="🚨")
    else:
        st.success("Answer approved by the critic.", icon="✅")

    st.markdown(response.get("text") or "_No answer text returned._")

    citations = response.get("citations") or []
    if citations:
        with st.expander(f"Citations ({len(citations)})", expanded=False):
            for i, cite in enumerate(citations, start=1):
                st.markdown(
                    f"**{i}. `{cite.get('doc_id')}`** — score `{cite.get('score'):.3f}`"
                )
                st.caption(cite.get("excerpt", ""))

    packet = response.get("escalation_packet")
    if packet:
        with st.expander("Escalation packet", expanded=escalated):
            st.json(packet)

    st.caption(f"trace_id: `{result.get('trace_id', '—')}`")


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #
def main() -> None:
    st.set_page_config(page_title="InsightDesk", page_icon="🛟", layout="centered")
    st.session_state.setdefault("api_base", DEFAULT_API_BASE)

    st.title("🛟 InsightDesk")
    st.caption("Agentic customer-support assistant — retrieve, compose, critique, escalate.")

    with st.sidebar:
        st.header("Settings")
        st.session_state.api_base = st.text_input("Backend URL", st.session_state.api_base)
        user_id = st.text_input("User id (optional)", value="user-123")

        healthy, detail = check_health()
        st.markdown(
            f"**Backend:** {'🟢 online' if healthy else '🔴 offline'}  \n`{detail}`"
        )

        if st.button("Ingest knowledge base", use_container_width=True, disabled=not healthy):
            try:
                with st.spinner("Ingesting documents…"):
                    out = ingest()
                st.success(f"Ingested {out.get('count', 0)} documents.")
            except requests.RequestException as exc:
                st.error(f"Ingest failed: {exc}")

    if not healthy:
        st.error(
            "Backend is not reachable. Start it with "
            "`uvicorn app.main:app --reload`, then check the URL in the sidebar."
        )
        return

    tab_ask, tab_docs = st.tabs(["Ask a question", "Lookup document"])

    with tab_ask:
        with st.form("ask"):
            query = st.text_area(
                "Customer question",
                placeholder="How do I export my data?",
                height=120,
            )
            submitted = st.form_submit_button("Ask InsightDesk", use_container_width=True)

        if submitted:
            if not query.strip():
                st.warning("Please enter a question.")
            else:
                try:
                    with st.spinner("Thinking…"):
                        result = process_query(query.strip(), user_id.strip() or None)
                    render_answer(result)
                except requests.RequestException as exc:
                    st.error(f"Request failed: {exc}")

    with tab_docs:
        doc_id = st.text_input("Document id", placeholder="doc-1")
        if st.button("Fetch document", disabled=not doc_id.strip()):
            try:
                doc = fetch_doc(doc_id.strip())
            except requests.RequestException as exc:
                st.error(f"Request failed: {exc}")
            else:
                if doc is None:
                    st.warning(f"No document found for id `{doc_id.strip()}`.")
                else:
                    st.subheader(doc.get("title", doc_id))
                    if doc.get("source"):
                        st.caption(f"source: {doc['source']}")
                    st.markdown(doc.get("content", "_empty_"))


if __name__ == "__main__":
    main()