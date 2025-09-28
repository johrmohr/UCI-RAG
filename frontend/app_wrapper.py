#!/usr/bin/env python3
"""
App wrapper that loads the correct RAG pipeline based on available dependencies
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the appropriate RAG pipeline based on environment
if os.environ.get('USE_LITE_MODE') == 'True':
    from rag_pipeline.rag_system_lite import RAGPipelineLite as RAGPipeline
else:
    from rag_pipeline.rag_system import RAGPipeline

# Import the rest of the app components
import streamlit as st
import time
from datetime import datetime

# Import the UI components and main function from app.py
def load_css():
    """Load custom CSS styling"""
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

        /* Text colors */
        .stMarkdown {
            color: #e8eaed;
        }

        h2, h3, h4, h5, h6 {
            color: #e8eaed !important;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""

    # Load custom CSS
    load_css()

    # Title - Clean, no emoji
    st.markdown(
        '<h1>UCI Research Intelligence System</h1>',
        unsafe_allow_html=True
    )

    # Simple subtitle without mode indicator
    st.markdown(
        '<p style="text-align: center; color: #969ba1; font-size: 1.1rem;">AI-Powered Research Discovery</p>',
        unsafe_allow_html=True
    )

    # Initialize RAG pipeline
    if 'rag' not in st.session_state:
        try:
            st.session_state.rag = RAGPipeline()
        except Exception as e:
            st.error(f"Error initializing RAG pipeline: {str(e)}")
            st.session_state.rag = None

    # Search interface
    st.markdown('<div class="search-wrapper">', unsafe_allow_html=True)
    col1, col2 = st.columns([5, 1])

    with col1:
        query = st.text_input(
            "Search research papers",
            placeholder="e.g., 'quantum computing applications' or 'dark matter detection methods'",
            label_visibility="collapsed",
            key="search_input"
        )

    with col2:
        search_button = st.button("Search", type="primary", key="search_button")

    st.markdown('</div>', unsafe_allow_html=True)

    # Sample queries - no emojis
    st.markdown("##### Try these sample queries:")
    col1, col2, col3, col4 = st.columns(4)

    sample_queries = [
        "Quantum computing",
        "Machine learning physics",
        "Dark matter research",
        "Condensed matter"
    ]

    for col, sample in zip([col1, col2, col3, col4], sample_queries):
        with col:
            if st.button(sample, key=f"sample_{sample}"):
                query = sample

    # Handle search
    if (search_button or query) and query and st.session_state.rag:
        with st.spinner("Searching research corpus..."):
            try:
                # Query the RAG pipeline
                start_time = time.time()
                results = st.session_state.rag.query(query, k=5)
                elapsed_time = time.time() - start_time

                # Display results - no success message with emoji
                st.markdown(f"Found relevant research in {elapsed_time:.2f} seconds")

                # Display AI Summary first (not in tabs)
                st.markdown("---")
                st.markdown("### Summary")
                if 'answer' in results:
                    st.markdown(results['answer'])
                else:
                    st.info("No AI summary available.")

                # Then display Research Papers
                st.markdown("---")
                st.markdown("### Relevant Research Papers")

                if 'source_papers' in results and results['source_papers']:
                    for i, paper in enumerate(results['source_papers'][:5], 1):
                        st.markdown(f"#### Paper {i}: {paper.get('title', 'Unknown Title')}")

                        # Paper metadata in a clean format
                        st.markdown(f"**Authors:** {', '.join(paper.get('authors', ['Unknown']))}")
                        st.markdown(f"**Year:** {paper.get('year', 'N/A')}")

                        if 'arxiv_id' in paper:
                            st.markdown(f"**arXiv ID:** {paper['arxiv_id']}")

                        # Abstract
                        st.markdown("**Abstract:**")
                        abstract = paper.get('abstract', 'No abstract available')
                        # Show more of the abstract
                        st.markdown(abstract[:800] + "..." if len(abstract) > 800 else abstract)

                        # Relevance score as a simple metric
                        if 'relevance_score' in paper:
                            st.markdown(f"**Relevance Score:** {paper['relevance_score']:.2%}")

                        st.markdown("---")
                else:
                    st.info("No papers found for this query.")

            except Exception as e:
                st.error(f"Error during search: {str(e)}")

    # No footer with system stats - completely removed

if __name__ == "__main__":
    main()