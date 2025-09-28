#!/usr/bin/env python3
"""
UCI Research Intelligence System - Streamlit Cloud Deployment
Entry point that loads the main frontend app
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Page configuration - hide sidebar completely
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

# Import and run the main app
from frontend.app import main
main()