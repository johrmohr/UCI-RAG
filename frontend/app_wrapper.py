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

    # Title
    st.markdown(
        '<h1>🔬 UCI Research Intelligence System</h1>',
        unsafe_allow_html=True
    )

    # Subtitle with mode indicator
    if os.environ.get('USE_LITE_MODE') == 'True':
        st.markdown(
            '<p style="text-align: center; color: #969ba1; font-size: 1.1rem;">AI-Powered Research Discovery (Demo Mode)</p>',
            unsafe_allow_html=True
        )
    else:
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

    # Sample queries
    st.markdown("##### Try these sample queries:")
    col1, col2, col3, col4 = st.columns(4)

    sample_queries = [
        "🔬 Quantum computing",
        "🧬 Machine learning in physics",
        "🌌 Dark matter research",
        "⚛️ Condensed matter physics"
    ]

    for col, sample in zip([col1, col2, col3, col4], sample_queries):
        with col:
            if st.button(sample, key=f"sample_{sample}"):
                query = sample.replace("🔬 ", "").replace("🧬 ", "").replace("🌌 ", "").replace("⚛️ ", "")

    # Handle search
    if (search_button or query) and query and st.session_state.rag:
        with st.spinner("Searching research corpus..."):
            try:
                # Query the RAG pipeline
                start_time = time.time()
                results = st.session_state.rag.query(query, k=5)
                elapsed_time = time.time() - start_time

                # Display results
                st.success(f"✅ Found relevant research! ({elapsed_time:.2f}s)")

                # Create tabs for results
                tab1, tab2, tab3 = st.tabs(["📄 Research Papers", "🤖 AI Summary", "📊 Query Stats"])

                with tab1:
                    if 'source_papers' in results and results['source_papers']:
                        for i, paper in enumerate(results['source_papers'][:5]):
                            with st.expander(f"📄 {paper.get('title', 'Unknown Title')}", expanded=(i==0)):
                                # Paper metadata
                                st.markdown(f"**Authors:** {', '.join(paper.get('authors', ['Unknown']))}")
                                st.markdown(f"**Year:** {paper.get('year', 'N/A')}")
                                if 'arxiv_id' in paper:
                                    st.markdown(f"**arXiv ID:** {paper['arxiv_id']}")

                                # Abstract
                                st.markdown("**Abstract:**")
                                st.markdown(paper.get('abstract', 'No abstract available')[:500] + "...")

                                # Relevance score
                                if 'relevance_score' in paper:
                                    st.progress(paper['relevance_score'], text=f"Relevance: {paper['relevance_score']:.2%}")
                    else:
                        st.info("No papers found for this query.")

                with tab2:
                    st.markdown("### AI-Generated Summary")
                    if 'answer' in results:
                        st.markdown(results['answer'])
                    else:
                        st.info("No AI summary available.")

                with tab3:
                    st.markdown("### Query Statistics")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Papers Retrieved", results.get('papers_used', 0))

                    with col2:
                        st.metric("Response Time", f"{elapsed_time:.2f}s")

                    with col3:
                        if 'cost_estimate' in results:
                            cost = results['cost_estimate'].get('total_cost', 0)
                            st.metric("Query Cost", f"${cost:.4f}")
                        else:
                            st.metric("Query Cost", "N/A")

                    if 'confidence' in results:
                        st.progress(results['confidence'], text=f"Confidence: {results['confidence']:.2%}")

            except Exception as e:
                st.error(f"Error during search: {str(e)}")

    # Footer with system info
    st.markdown("---")

    if st.session_state.rag:
        try:
            stats = st.session_state.rag.get_stats()
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Papers Indexed", stats.get('papers_indexed', 'N/A'))

            with col2:
                st.metric("Embedding Model", stats.get('embedding_model', 'N/A'))

            with col3:
                st.metric("LLM Model", stats.get('llm_model', 'N/A'))

            with col4:
                st.metric("System Status", stats.get('status', 'N/A'))
        except:
            pass

    # Add disclaimer for demo mode
    if os.environ.get('USE_LITE_MODE') == 'True':
        st.info("🔔 Running in demo mode with sample data. Full functionality requires ML dependencies.")

if __name__ == "__main__":
    main()