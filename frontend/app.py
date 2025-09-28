#!/usr/bin/env python3
"""
UCI Research Intelligence System - Streamlit Frontend
Professional demo application for showcasing RAG capabilities
"""

import streamlit as st
import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag_pipeline.rag_system import RAGPipeline

# Page configuration
st.set_page_config(
    page_title="UCI Research Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Simplified and reliable
def load_css():
    st.markdown("""
    <style>
        /* Dark background */
        .stApp {
            background-color: #202124;
        }

        /* White title */
        h1 {
            color: #ffffff !important;
            text-align: center;
            font-weight: 400;
            font-size: 2.5rem;
            margin-bottom: 2rem;
        }

        /* Search container styling */
        .search-wrapper {
            max-width: 700px;
            margin: 0 auto;
        }

        /* Style the text input */
        .stTextInput > div > div > input {
            background: #303134 !important;
            border: 1px solid #5f6368 !important;
            border-radius: 24px !important;
            padding: 12px 20px !important;
            color: #e8eaed !important;
            font-size: 16px !important;
        }

        .stTextInput > div > div > input::placeholder {
            color: #969ba1 !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #8ab4f8 !important;
            box-shadow: 0 1px 6px 0 rgba(32,33,36,.28) !important;
        }

        /* Style the search button */
        .stButton > button {
            background: #8ab4f8 !important;
            color: #202124 !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 10px 24px !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            margin-left: 10px;
        }

        .stButton > button:hover {
            background: #aecbfa !important;
            box-shadow: 0 1px 6px 0 rgba(32,33,36,.28) !important;
        }

        /* Sample queries buttons */
        .sample-button {
            background: #303134;
            border: 1px solid #5f6368;
            border-radius: 16px;
            padding: 8px 16px;
            margin: 4px;
            color: #8ab4f8;
            font-size: 13px;
            cursor: pointer;
            display: inline-block;
        }

        .sample-button:hover {
            background: #3c4043;
            border-color: #8ab4f8;
        }

        /* Result cards */
        .result-card {
            background: #303134;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid #5f6368;
            color: #e8eaed;
        }

        .paper-card {
            background: #303134;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            border: 1px solid #5f6368;
            color: #e8eaed;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #171717;
            border-right: 1px solid #5f6368;
        }

        section[data-testid="stSidebar"] .stMarkdown {
            color: #e8eaed;
        }

        section[data-testid="stSidebar"] button {
            color: #8ab4f8 !important;
            background: transparent !important;
            border: none !important;
            text-align: left !important;
            padding: 8px 12px !important;
            font-size: 14px !important;
        }

        section[data-testid="stSidebar"] button:hover {
            background: rgba(138,180,248,.08) !important;
        }

        /* Text colors */
        .stMarkdown {
            color: #e8eaed;
        }

        h2, h3, h4, h5, h6 {
            color: #e8eaed !important;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background: #303134 !important;
            color: #e8eaed !important;
            border-radius: 8px !important;
            border: 1px solid #5f6368 !important;
        }

        .streamlit-expanderContent {
            background: #303134 !important;
            border: 1px solid #5f6368 !important;
            border-top: none !important;
            color: #e8eaed !important;
        }

        /* Footer */
        .footer {
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid #5f6368;
            text-align: center;
            color: #9aa0a6;
            font-size: 0.8rem;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'pipeline' not in st.session_state:
        with st.spinner("Initializing Research Intelligence System..."):
            st.session_state.pipeline = RAGPipeline()

    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

    if 'current_results' not in st.session_state:
        st.session_state.current_results = None

    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

# Sample queries
SAMPLE_QUERIES = [
    "What are the latest developments in quantum computing?",
    "Find research on topological materials",
    "Who is working on dark matter detection?",
    "Summarize gravitational wave research",
    "Explain recent advances in superconductivity"
]

def display_sidebar():
    """Display sidebar with search history"""
    with st.sidebar:
        st.markdown("### Recents")
        if st.session_state.search_history:
            for item in reversed(st.session_state.search_history[-10:]):
                query_text = item['query']
                display_text = query_text[:40] + "..." if len(query_text) > 40 else query_text
                if st.button(display_text, key=f"history_{item['timestamp']}", use_container_width=True):
                    st.session_state.search_query = query_text
                    st.rerun()
        else:
            st.markdown("No recent searches")

def display_results(results):
    """Display search results"""
    if not results:
        return

    st.markdown("### Answer")

    # Display answer
    answer_html = f"""
    <div class="result-card">
        {results['answer']}
    </div>
    """
    st.markdown(answer_html, unsafe_allow_html=True)

    # Display papers
    if results.get('papers'):
        with st.expander(f"Retrieved Papers ({len(results['papers'])})", expanded=True):
            for i, paper in enumerate(results['papers'], 1):
                paper_html = f"""
                <div class="paper-card">
                    <strong>{i}. {paper['title']}</strong><br/>
                    <small style="color: #9aa0a6;">Authors: {', '.join(paper['authors'][:3]) if paper['authors'] else 'N/A'}</small><br/>
                    <small style="color: #9aa0a6;">Year: {paper['year']} | Relevance: {paper['relevance_score']:.3f}</small><br/>
                    <details>
                        <summary style="cursor: pointer; color: #8ab4f8;">View Abstract</summary>
                        <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #bdc1c6;">{paper['abstract']}</p>
                    </details>
                </div>
                """
                st.markdown(paper_html, unsafe_allow_html=True)

def main():
    """Main application"""
    # Initialize
    init_session_state()
    load_css()

    # Display sidebar
    display_sidebar()

    # Title
    st.markdown("<h1>UCI Research Intelligence System</h1>", unsafe_allow_html=True)

    # Search interface - Simple and reliable
    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        # Search input and button on same row
        search_col, btn_col = st.columns([4, 1])

        with search_col:
            query = st.text_input(
                "",
                placeholder="Ask about research papers...",
                key="search_input",
                value=st.session_state.search_query,
                label_visibility="collapsed"
            )

        with btn_col:
            search_clicked = st.button("Search", type="primary")

        # Sample queries as clickable options below search
        st.markdown("**Try these sample queries:**")

        # Create sample query buttons
        cols = st.columns(3)
        for idx, sample_query in enumerate(SAMPLE_QUERIES):
            with cols[idx % 3]:
                if st.button(sample_query[:30] + "...", key=f"sample_{idx}", help=sample_query):
                    st.session_state.search_query = sample_query
                    st.rerun()

    # Handle search
    if search_clicked and query:
        with st.spinner("Analyzing research papers..."):
            start_time = time.time()

            try:
                results = st.session_state.pipeline.generate_answer(
                    query,
                    search_papers=True,
                    search_faculty=False,
                    paper_top_k=5,
                    faculty_top_k=0
                )

                results['search_time'] = time.time() - start_time
                results['query'] = query
                results['timestamp'] = datetime.now().strftime("%Y%m%d_%H%M%S")

                st.session_state.current_results = results
                st.session_state.search_history.append(results)

                # Keep only last 10 searches
                if len(st.session_state.search_history) > 10:
                    st.session_state.search_history = st.session_state.search_history[-10:]

                # Clear the search query
                st.session_state.search_query = ""

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Tip: Make sure ChromaDB is running and AWS credentials are configured")

    # Display current results
    if st.session_state.current_results:
        display_results(st.session_state.current_results)

    # Footer
    st.markdown("""
    <div class="footer">
        Note: This is a demo application for educational purposes.<br/>
        The research papers used are from online sources and not actual UCI research.<br/>
        © 2024 Jordan Moreno
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()