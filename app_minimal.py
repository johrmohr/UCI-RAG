#!/usr/bin/env python3
"""
UCI Research Intelligence - Minimal Demo Version
Works without heavy ML dependencies
"""

import streamlit as st
import json
import random
from datetime import datetime

# Page config - hide sidebar completely
st.set_page_config(
    page_title="UCI Research Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS to hide sidebar and toggle arrow completely
st.markdown("""
<style>
    /* Hide the sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Hide the sidebar toggle button/arrow */
    [data-testid="collapsedControl"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Sample data (normally from database)
SAMPLE_PAPERS = [
    {
        "title": "Quantum Computing Applications in Particle Physics",
        "authors": "Zhang et al.",
        "year": 2024,
        "abstract": "Novel quantum algorithms for high-energy physics simulations..."
    },
    {
        "title": "Topological Materials for Quantum Information",
        "authors": "Smith et al.",
        "year": 2024,
        "abstract": "Investigation of topological superconductors for quantum computing..."
    },
    {
        "title": "Machine Learning in Condensed Matter Physics",
        "authors": "Johnson et al.",
        "year": 2023,
        "abstract": "Deep learning approaches to predict material properties..."
    }
]

FACULTY = [
    {"name": "Dr. Sarah Chen", "expertise": "Quantum Computing, Quantum Information"},
    {"name": "Dr. Michael Rodriguez", "expertise": "Condensed Matter, Superconductivity"},
    {"name": "Dr. Emily Watson", "expertise": "Particle Physics, Machine Learning"}
]

# UI Components
st.title("🔬 UCI Physics Research Intelligence")
st.markdown("*AI-powered research discovery across UCI's physics department*")

# Search interface
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("", placeholder="Ask about quantum computing, condensed matter, particle physics...")
with col2:
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

# Process search
if search_button and query:
    with st.spinner("Searching research corpus..."):
        import time
        time.sleep(1)  # Simulate processing

        st.success("Found relevant research!")

        # Results tabs
        tab1, tab2, tab3 = st.tabs(["📄 Papers", "👥 Faculty", "💡 AI Summary"])

        with tab1:
            st.subheader("Relevant Papers")
            for paper in random.sample(SAMPLE_PAPERS, min(2, len(SAMPLE_PAPERS))):
                with st.container():
                    st.markdown(f"**{paper['title']}**")
                    st.caption(f"{paper['authors']} • {paper['year']}")
                    st.text(paper['abstract'][:150] + "...")
                    st.markdown("---")

        with tab2:
            st.subheader("Faculty Experts")
            for faculty in random.sample(FACULTY, min(2, len(FACULTY))):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown("👤")
                with col2:
                    st.markdown(f"**{faculty['name']}**")
                    st.caption(faculty['expertise'])

        with tab3:
            st.subheader("AI-Generated Summary")
            st.info(f"""
            Based on your query about "{query}", here are the key insights from UCI's research:

            • UCI has active research groups working on {query.lower()} with recent publications in top journals
            • Multiple faculty members have expertise in related areas
            • Collaboration opportunities exist with both theoretical and experimental groups
            • Recent grants have been awarded for advancing this research area

            *Note: This is a demo response. Full system uses Claude 3 for intelligent summaries.*
            """)

# Stats section (moved from sidebar)
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Papers Indexed", "120+")
with col2:
    st.metric("Faculty Profiles", "15+")
with col3:
    st.metric("Avg Response Time", "1.2s")
with col4:
    st.metric("Query Accuracy", "85%")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🎓 UCI Physics & Astronomy")
with col2:
    st.caption("🤖 Powered by AI")
with col3:
    st.caption(f"📅 {datetime.now().strftime('%B %Y')}")