#!/bin/bash

# ============================================================================
# UCI Research Intelligence - Environment Setup Script for macOS
# ============================================================================
# This script sets up the complete Python environment for the UCI Research
# Intelligence System on macOS, including virtual environment creation,
# dependency installation, and verification.
#
# Requirements:
# - macOS (Darwin)
# - Python 3.9 or higher
# - Homebrew (will prompt to install if missing)
#
# Usage:
#   ./setup_environment.sh
#
# Author: UCI Research Intelligence Team
# Date: 2025-01-21
# ============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function for colored output
print_header() {
    echo -e "\n${CYAN}${BOLD}============================================================${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}============================================================${NC}\n"
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_step() {
    echo -e "${MAGENTA}[→]${NC} $1"
}

# ASCII Art Logo
print_logo() {
    echo -e "${CYAN}"
    cat << "EOF"
    _   _  ____ ___   ____                               _
   | | | |/ ___|_ _| |  _ \ ___  ___  ___  __ _ _ __ ___| |__
   | | | | |    | |  | |_) / _ \/ __|/ _ \/ _` | '__/ __| '_ \
   | |_| | |___ | |  |  _ <  __/\__ \  __/ (_| | | | (__| | | |
    \___/ \____|___| |_| \_\___||___/\___|\__,_|_|  \___|_| |_|

    Intelligence System - Environment Setup
EOF
    echo -e "${NC}"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script is designed for macOS only."
        print_info "Detected OS: $OSTYPE"
        exit 1
    fi
    print_status "macOS detected: $(sw_vers -productVersion)"
}

# Check Python version
check_python() {
    print_step "Checking Python installation..."

    # Check for Python 3.9+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [[ $PYTHON_MAJOR -eq 3 ]] && [[ $PYTHON_MINOR -ge 9 ]]; then
            print_status "Python $PYTHON_VERSION found (meets requirement: 3.9+)"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.9+ required, but $PYTHON_VERSION found"
            print_info "Install Python 3.9+ using: brew install python@3.9"
            exit 1
        fi
    else
        print_error "Python 3 not found"
        print_info "Install Python using: brew install python@3.9"
        exit 1
    fi
}

# Check for Homebrew
check_homebrew() {
    print_step "Checking for Homebrew..."

    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew not found"
        read -p "Would you like to install Homebrew? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            print_status "Homebrew installed"
        else
            print_warning "Homebrew is recommended for dependency management"
        fi
    else
        print_status "Homebrew found: $(brew --version | head -n 1)"
    fi
}

# Create virtual environment
create_venv() {
    print_header "Creating Python Virtual Environment"

    VENV_DIR="venv"

    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists at ./$VENV_DIR"
        read -p "Do you want to recreate it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_step "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        else
            print_info "Using existing virtual environment"
            return
        fi
    fi

    print_step "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR

    if [ -d "$VENV_DIR" ]; then
        print_status "Virtual environment created successfully"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    print_step "Activating virtual environment..."

    # Source the activation script
    source venv/bin/activate

    # Verify activation
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_status "Virtual environment activated"
        print_info "Python: $(which python)"
        print_info "Pip: $(which pip)"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
}

# Upgrade pip and install wheel
upgrade_pip() {
    print_header "Upgrading pip and Installing Build Tools"

    print_step "Upgrading pip..."
    pip install --upgrade pip

    print_step "Installing wheel and setuptools..."
    pip install --upgrade wheel setuptools

    print_status "Build tools ready"
}

# Install requirements
install_requirements() {
    print_header "Installing Python Dependencies"

    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi

    print_info "This may take 5-10 minutes depending on your internet speed..."
    print_info "Installing packages from requirements.txt..."

    # Install in chunks to better handle failures
    print_step "Installing AWS and core dependencies..."
    pip install boto3 botocore awscli python-dotenv

    print_step "Installing data processing libraries..."
    pip install pandas numpy scipy scikit-learn

    print_step "Installing AI/ML libraries (this may take a while)..."
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install transformers sentence-transformers

    print_step "Installing remaining dependencies..."
    pip install -r requirements.txt

    print_status "All dependencies installed successfully"
}

# Create .env file
create_env_file() {
    print_header "Creating Environment Configuration"

    ENV_FILE=".env"

    if [ -f "$ENV_FILE" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to create a new one? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing .env file"
            return
        fi
    fi

    print_step "Creating .env file..."

    cat > $ENV_FILE << 'EOF'
# ============================================================================
# UCI Research Intelligence - Environment Configuration
# ============================================================================
# Copy this file to .env and fill in your actual values
# DO NOT commit .env to version control!

# ==================== AWS Configuration ====================
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-west-2
AWS_PROFILE=default

# ==================== S3 Configuration ====================
S3_BUCKET_NAME=uci-research-poc-XXXXX  # Will be set by s3_setup.py
S3_DATA_PREFIX=raw-data/
S3_EMBEDDINGS_PREFIX=embeddings/
S3_METADATA_PREFIX=metadata/
S3_LOGS_PREFIX=logs/

# ==================== OpenSearch Configuration ====================
OPENSEARCH_ENDPOINT=https://your-domain.us-west-2.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_INDEX_NAME=uci-research-documents
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your_password_here

# ==================== Vector Database Configuration ====================
# ChromaDB (local)
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=uci_research

# Pinecone (cloud)
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=uci-research

# ==================== LLM Configuration ====================
# OpenAI
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229

# AWS Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-west-2

# ==================== Database Configuration ====================
DATABASE_URL=postgresql://user:password@localhost:5432/uci_research
REDIS_URL=redis://localhost:6379/0

# ==================== Application Configuration ====================
APP_NAME=UCI Research Intelligence
APP_VERSION=0.1.0
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO

# ==================== Security Configuration ====================
SECRET_KEY=your_secret_key_here_change_in_production
JWT_SECRET_KEY=your_jwt_secret_here_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ==================== API Configuration ====================
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=True

# ==================== Frontend Configuration ====================
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
STREAMLIT_THEME=light

# ==================== Monitoring Configuration ====================
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_PORT=9090

# ==================== Feature Flags ====================
ENABLE_CACHING=True
ENABLE_RATE_LIMITING=True
ENABLE_METRICS=True
ENABLE_TRACING=False

# ==================== Resource Limits ====================
MAX_UPLOAD_SIZE_MB=100
MAX_QUERY_RESULTS=100
MAX_EMBEDDING_BATCH_SIZE=32
MAX_CONCURRENT_REQUESTS=10

# ==================== Cost Controls ====================
MONTHLY_BUDGET_USD=120
DAILY_BUDGET_USD=4
ALERT_EMAIL=your_email@uci.edu
EOF

    print_status ".env template created"
    print_warning "Remember to update .env with your actual credentials!"
}

# Verify imports
verify_imports() {
    print_header "Verifying Package Imports"

    print_step "Creating import verification script..."

    cat > verify_imports.py << 'EOF'
#!/usr/bin/env python3
"""Verify all required packages can be imported"""

import sys
import importlib
from typing import List, Tuple

def check_imports() -> Tuple[List[str], List[str]]:
    """Check if all required packages can be imported"""

    packages = [
        # AWS
        ('boto3', 'AWS SDK'),
        ('botocore', 'AWS Core'),

        # Data Processing
        ('pandas', 'Data Analysis'),
        ('numpy', 'Numerical Computing'),
        ('scipy', 'Scientific Computing'),
        ('sklearn', 'Machine Learning'),

        # Data Generation
        ('faker', 'Synthetic Data'),

        # Document Processing
        ('PyPDF2', 'PDF Processing'),
        ('docx', 'Word Documents'),
        ('bs4', 'Web Scraping'),

        # Vector Search
        ('opensearchpy', 'OpenSearch'),
        ('sentence_transformers', 'Embeddings'),
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('faiss', 'Vector Search'),
        ('chromadb', 'ChromaDB'),

        # RAG & LLM
        ('langchain', 'LangChain'),
        ('openai', 'OpenAI SDK'),
        ('anthropic', 'Anthropic SDK'),

        # Frontend
        ('streamlit', 'Streamlit UI'),
        ('plotly', 'Interactive Plots'),

        # Backend
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'ASGI Server'),
        ('pydantic', 'Data Validation'),

        # Database
        ('sqlalchemy', 'SQL ORM'),
        ('redis', 'Redis Cache'),

        # Utilities
        ('dotenv', 'Environment Variables'),
        ('yaml', 'YAML Config'),
        ('click', 'CLI Framework'),
        ('tqdm', 'Progress Bars'),
        ('rich', 'Terminal Formatting'),
    ]

    success = []
    failed = []

    for package, description in packages:
        try:
            # Handle special import names
            if package == 'sklearn':
                importlib.import_module('sklearn')
            elif package == 'docx':
                importlib.import_module('docx')
            elif package == 'bs4':
                importlib.import_module('bs4')
            elif package == 'opensearchpy':
                importlib.import_module('opensearchpy')
            elif package == 'dotenv':
                importlib.import_module('dotenv')
            elif package == 'yaml':
                importlib.import_module('yaml')
            else:
                importlib.import_module(package)
            success.append(f"✅ {description:20} ({package})")
        except ImportError as e:
            failed.append(f"❌ {description:20} ({package}): {str(e)}")

    return success, failed

def main():
    print("\n" + "="*60)
    print("IMPORT VERIFICATION")
    print("="*60 + "\n")

    success, failed = check_imports()

    print("Successful imports:")
    for item in success:
        print(f"  {item}")

    if failed:
        print("\nFailed imports:")
        for item in failed:
            print(f"  {item}")
        print(f"\n❌ {len(failed)} packages failed to import")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(success)} packages imported successfully!")

    # Check Python version
    print(f"\nPython version: {sys.version}")

    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")

if __name__ == "__main__":
    main()
EOF

    print_step "Running import verification..."
    python verify_imports.py

    if [ $? -eq 0 ]; then
        print_status "All imports verified successfully"
    else
        print_error "Some imports failed - check error messages above"
        print_info "Try: pip install -r requirements.txt"
    fi
}

# Create project structure verification
verify_structure() {
    print_header "Verifying Project Structure"

    directories=(
        "data_generation"
        "aws_infrastructure"
        "embeddings"
        "search"
        "rag_pipeline"
        "frontend"
        "config"
        "tests"
        "docs"
    )

    all_exist=true
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            print_status "Directory exists: $dir/"
        else
            print_warning "Directory missing: $dir/"
            all_exist=false
        fi
    done

    if [ "$all_exist" = true ]; then
        print_status "All project directories present"
    else
        print_warning "Some directories are missing - they will be created as needed"
    fi
}

# Create activation helper script
create_activation_script() {
    print_step "Creating activation helper script..."

    cat > activate.sh << 'EOF'
#!/bin/bash
# Quick activation script for UCI Research Intelligence environment

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    echo "   Python: $(which python)"
    echo "   Project: UCI Research Intelligence"
else
    echo "❌ Virtual environment not found. Run setup_environment.sh first."
fi
EOF

    chmod +x activate.sh
    print_status "Created activate.sh helper script"
}

# Main execution
main() {
    clear
    print_logo

    print_info "Starting environment setup for UCI Research Intelligence System"
    print_info "This process will take approximately 5-10 minutes"
    echo

    # System checks
    check_macos
    check_homebrew
    check_python

    # Virtual environment setup
    create_venv
    activate_venv
    upgrade_pip

    # Install dependencies
    install_requirements

    # Configuration
    create_env_file

    # Verification
    verify_imports
    verify_structure

    # Helper scripts
    create_activation_script

    # Success summary
    print_header "🎉 Setup Complete!"

    echo -e "${GREEN}${BOLD}Environment setup completed successfully!${NC}\n"

    print_info "Quick Start Commands:"
    echo
    echo "  1. Activate environment:"
    echo "     ${CYAN}source venv/bin/activate${NC}"
    echo "     or use the helper: ${CYAN}./activate.sh${NC}"
    echo
    echo "  2. Configure AWS (if not done):"
    echo "     ${CYAN}./aws_infrastructure/setup_aws.sh${NC}"
    echo
    echo "  3. Set up AWS resources:"
    echo "     ${CYAN}python aws_infrastructure/iam_setup.py${NC}"
    echo "     ${CYAN}python aws_infrastructure/s3_setup.py${NC}"
    echo "     ${CYAN}python aws_infrastructure/cost_monitoring.py${NC}"
    echo
    echo "  4. Update .env file with your credentials:"
    echo "     ${CYAN}nano .env${NC}"
    echo
    echo "  5. Run Streamlit app (when ready):"
    echo "     ${CYAN}streamlit run frontend/app.py${NC}"
    echo
    echo "  6. Start API server (when ready):"
    echo "     ${CYAN}uvicorn rag_pipeline.api:app --reload${NC}"
    echo

    print_info "Documentation: docs/README.md"
    print_info "Support: uci-research@uci.edu"

    echo -e "\n${BOLD}Happy researching! 🚀${NC}\n"
}

# Run main function
main