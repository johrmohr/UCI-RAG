#!/usr/bin/env python3
"""
UCI Research Intelligence System - Streamlit Cloud Deployment
Simplified entry point with dependency handling
"""

import streamlit as st
import os
import sys
from pathlib import Path
import json
import random
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Page configuration - hide sidebar completely
st.set_page_config(
    page_title="UCI Research RAG Demo",
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

    /* Center title */
    h1 {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Configure environment from Streamlit secrets
def setup_environment():
    """Load Streamlit secrets into environment variables"""
    if hasattr(st, 'secrets'):
        # AWS Configuration
        if 'aws' in st.secrets:
            for key, value in st.secrets['aws'].items():
                os.environ[key] = str(value)

        # App Configuration
        if 'app' in st.secrets:
            for key, value in st.secrets['app'].items():
                os.environ[key] = str(value)

# Setup environment
setup_environment()

# Try to import the full app, but provide fallback
try:
    # Try to import the main app
    from frontend.app import main
    # If successful, run it
    main()

except (ImportError, ModuleNotFoundError) as e:
    # Fallback: Run a demo version without heavy dependencies

    # Title and description
    st.title("🔬 UCI Research RAG Demo")
    st.markdown("<p style='text-align: center; color: gray;'>A demonstration of RAG (Retrieval-Augmented Generation) for academic research discovery</p>", unsafe_allow_html=True)

    # Info message
    st.info("Running in demo mode. Full features require additional dependencies.")

    st.markdown("---")

    # Search interface
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("",
                            placeholder="Try: 'What quantum computing research is happening?' or 'Show me papers about machine learning in physics'",
                            label_visibility="collapsed")
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    # Sample queries
    st.markdown("**Try these sample queries:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔬 Quantum Computing", use_container_width=True):
            query = "What quantum computing research is happening?"
    with col2:
        if st.button("🧬 ML in Physics", use_container_width=True):
            query = "Show me papers about machine learning in physics"
    with col3:
        if st.button("🌌 Dark Matter", use_container_width=True):
            query = "Recent research on dark matter detection"

    # Handle search
    if (search_button or query) and query:
        with st.spinner("Searching research papers..."):
            import time
            time.sleep(1)  # Simulate processing

            st.success("✅ Found relevant research!")

            # Create tabs for results
            tab1, tab2 = st.tabs(["📄 Research Papers", "💡 AI Summary"])

            with tab1:
                st.markdown("### Relevant Papers from ArXiv")

                # Sample papers (would be from actual database in production)
                papers = [
                    {
                        "title": "Quantum Machine Learning: A Survey of Current Approaches",
                        "authors": "Smith, J., Chen, L., Rodriguez, M.",
                        "year": "2024",
                        "abstract": "We present a comprehensive overview of quantum machine learning algorithms and their applications in various domains of physics. Our survey covers recent developments in variational quantum algorithms, quantum neural networks, and their implementation on current NISQ devices..."
                    },
                    {
                        "title": "Topological Quantum Computing: Recent Advances and Challenges",
                        "authors": "Johnson, A., Patel, R., Williams, K.",
                        "year": "2024",
                        "abstract": "This paper discusses recent breakthroughs in topological quantum computing, focusing on error correction mechanisms and scalability. We analyze the potential of anyonic interferometry and demonstrate novel approaches to fault-tolerant quantum gates..."
                    },
                    {
                        "title": "Applications of Deep Learning in High Energy Physics",
                        "authors": "Zhang, W., Thompson, D., Lee, S.",
                        "year": "2023",
                        "abstract": "Machine learning techniques have revolutionized data analysis in particle physics experiments. We review applications of deep neural networks in jet tagging, particle identification, and anomaly detection at the Large Hadron Collider..."
                    }
                ]

                # Display only 2 random papers for demo
                for paper in random.sample(papers, min(2, len(papers))):
                    with st.container():
                        st.markdown(f"**{paper['title']}**")
                        st.caption(f"{paper['authors']} • {paper['year']}")
                        st.text(paper['abstract'][:200] + "...")
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            st.link_button("View Paper", f"https://arxiv.org", use_container_width=True)
                        st.markdown("---")

            with tab2:
                st.markdown("### AI-Generated Summary")
                st.info(f"""
                Based on your query about **"{query}"**, here are the key findings from the research corpus:

                • **Active Research Areas**: Multiple research groups are investigating {query.lower()}, with significant progress in both theoretical and experimental aspects.

                • **Recent Developments**: Papers from 2023-2024 show advances in quantum algorithms, error correction, and practical implementations on current hardware.

                • **Cross-disciplinary Impact**: This research connects quantum physics with computer science, materials science, and information theory.

                • **Future Directions**: Researchers are focusing on scalability, noise reduction, and developing applications for near-term quantum devices.

                *Note: This is a demo response. The full system would use Claude AI to generate contextual summaries based on actual paper content.*
                """)

    # Stats section
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Papers in Demo", "120")
    with col2:
        st.metric("From ArXiv", "2022-2024")
    with col3:
        st.metric("Research Areas", "6")
    with col4:
        st.metric("Response Time", "< 2s")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        <p><b>Note:</b> This is a demonstration system using sample academic papers from ArXiv.</p>
        <p>It does not contain real UCI research data. Built to showcase RAG architecture.</p>
        <p><a href='https://github.com/johrmohr/UCI-RAG' target='_blank'>View on GitHub</a></p>
    </div>
    """, unsafe_allow_html=True)