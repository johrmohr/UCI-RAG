#!/usr/bin/env python3
"""
UCI Research Intelligence System - Streamlit Cloud Deployment
Entry point for Streamlit Cloud deployment
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Configure environment from Streamlit secrets
def setup_environment():
    """Load Streamlit secrets into environment variables"""
    if hasattr(st, 'secrets'):
        # AWS Configuration
        if 'aws' in st.secrets:
            for key, value in st.secrets['aws'].items():
                os.environ[key] = str(value)

        # S3 Configuration
        if 's3' in st.secrets:
            for key, value in st.secrets['s3'].items():
                os.environ[key] = str(value)

        # App Configuration
        if 'app' in st.secrets:
            for key, value in st.secrets['app'].items():
                os.environ[key] = str(value)

        # Model Configuration
        if 'model' in st.secrets:
            for key, value in st.secrets['model'].items():
                os.environ[key] = str(value)

# Setup environment before importing app
setup_environment()

# Import and run the main app
from frontend.app import main

if __name__ == "__main__":
    main()