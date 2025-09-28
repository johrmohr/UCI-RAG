#!/bin/bash

# ============================================================================
# Install Missing Packages Script for macOS
# ============================================================================
# This script installs sentence-transformers and handles Mac-specific
# PyTorch/Metal configuration for optimal performance on Apple Silicon
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

# ============================================================================
# CHECK SYSTEM
# ============================================================================

print_header "🍎 MACOS PACKAGE INSTALLATION SCRIPT"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS only."
    print_info "Detected OS: $OSTYPE"
    exit 1
fi

print_status "macOS detected: $(sw_vers -productVersion)"

# Check if Apple Silicon or Intel
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    print_status "Apple Silicon Mac detected (M1/M2/M3)"
    IS_APPLE_SILICON=true
else
    print_status "Intel Mac detected"
    IS_APPLE_SILICON=false
fi

# ============================================================================
# ACTIVATE VIRTUAL ENVIRONMENT
# ============================================================================

print_header "🐍 VIRTUAL ENVIRONMENT CHECK"

# Check if we're already in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_status "Virtual environment already active: $VIRTUAL_ENV"
    VENV_PYTHON="python"
    VENV_PIP="pip"
else
    # Look for venv in current directory
    if [ -d "venv" ]; then
        print_step "Activating virtual environment..."
        source venv/bin/activate

        if [[ "$VIRTUAL_ENV" != "" ]]; then
            print_status "Virtual environment activated"
            VENV_PYTHON="python"
            VENV_PIP="pip"
        else
            print_error "Failed to activate virtual environment"
            exit 1
        fi
    else
        print_error "No virtual environment found in current directory"
        print_info "Please run ./setup_environment.sh first to create a virtual environment"
        exit 1
    fi
fi

# Show Python and pip info
print_info "Python: $(which $VENV_PYTHON)"
print_info "Python version: $($VENV_PYTHON --version)"
print_info "Pip: $(which $VENV_PIP)"

# ============================================================================
# CHECK CURRENT INSTALLATIONS
# ============================================================================

print_header "📦 CHECKING CURRENT PACKAGES"

# Function to check if a package is installed
check_package() {
    local package=$1
    if $VENV_PIP show $package &>/dev/null; then
        local version=$($VENV_PIP show $package | grep Version | cut -d' ' -f2)
        print_status "$package is installed (version: $version)"
        return 0
    else
        print_warning "$package is NOT installed"
        return 1
    fi
}

# Check current status
TORCH_INSTALLED=false
TRANSFORMERS_INSTALLED=false
SENTENCE_TRANSFORMERS_INSTALLED=false

if check_package "torch"; then
    TORCH_INSTALLED=true
    # Check if PyTorch has MPS (Metal Performance Shaders) support
    print_step "Checking PyTorch Metal support..."
    $VENV_PYTHON -c "import torch; print('MPS available:', torch.backends.mps.is_available())" 2>/dev/null || true
fi

if check_package "transformers"; then
    TRANSFORMERS_INSTALLED=true
fi

if check_package "sentence-transformers"; then
    SENTENCE_TRANSFORMERS_INSTALLED=true
fi

# ============================================================================
# INSTALL PYTORCH (IF NEEDED)
# ============================================================================

print_header "🔥 PYTORCH INSTALLATION"

if [ "$TORCH_INSTALLED" = false ]; then
    if [ "$IS_APPLE_SILICON" = true ]; then
        print_info "Installing PyTorch with Metal Performance Shaders (MPS) support for Apple Silicon..."
        print_warning "This may take a few minutes (PyTorch is ~150MB)..."

        # Install PyTorch with MPS support for Apple Silicon
        $VENV_PIP install torch torchvision torchaudio

        print_status "PyTorch installed with Metal acceleration support"
    else
        print_info "Installing PyTorch for Intel Mac..."
        print_warning "This may take a few minutes (PyTorch is ~150MB)..."

        # Install PyTorch for Intel Mac (CPU only)
        $VENV_PIP install torch torchvision torchaudio

        print_status "PyTorch installed (CPU version)"
    fi
else
    print_info "PyTorch already installed, checking for updates..."
    $VENV_PIP install --upgrade torch torchvision torchaudio
    print_status "PyTorch updated to latest version"
fi

# ============================================================================
# INSTALL TRANSFORMERS
# ============================================================================

print_header "🤖 TRANSFORMERS INSTALLATION"

if [ "$TRANSFORMERS_INSTALLED" = false ]; then
    print_info "Installing transformers library..."
    $VENV_PIP install transformers
    print_status "Transformers installed"
else
    print_info "Transformers already installed, checking for updates..."
    $VENV_PIP install --upgrade transformers
    print_status "Transformers updated"
fi

# ============================================================================
# INSTALL SENTENCE-TRANSFORMERS
# ============================================================================

print_header "📝 SENTENCE-TRANSFORMERS INSTALLATION"

if [ "$SENTENCE_TRANSFORMERS_INSTALLED" = false ]; then
    print_info "Installing sentence-transformers..."
    $VENV_PIP install sentence-transformers
    print_status "Sentence-transformers installed"
else
    print_info "Sentence-transformers already installed, checking for updates..."
    $VENV_PIP install --upgrade sentence-transformers
    print_status "Sentence-transformers updated"
fi

# ============================================================================
# INSTALL ADDITIONAL DEPENDENCIES
# ============================================================================

print_header "📚 ADDITIONAL DEPENDENCIES"

print_step "Installing/updating related packages..."

# Install additional useful packages for embeddings
$VENV_PIP install --upgrade scipy scikit-learn nltk

print_status "Additional dependencies installed"

# ============================================================================
# VERIFICATION
# ============================================================================

print_header "✅ VERIFICATION"

print_step "Creating verification script..."

cat > verify_sentence_transformers.py << 'EOF'
#!/usr/bin/env python3
"""Verify sentence-transformers installation"""

import sys
import platform

print("\n" + "="*60)
print("SENTENCE-TRANSFORMERS VERIFICATION")
print("="*60 + "\n")

# System info
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Machine: {platform.machine()}")
print()

# Check PyTorch
try:
    import torch
    print(f"✅ PyTorch version: {torch.__version__}")

    # Check for Apple Silicon MPS support
    if platform.machine() == 'arm64':
        if torch.backends.mps.is_available():
            print("✅ Metal Performance Shaders (MPS) available")
            if torch.backends.mps.is_built():
                print("✅ MPS support is built into PyTorch")
        else:
            print("⚠️  MPS not available (CPU mode will be used)")

    # Test tensor creation
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    x = torch.rand(5, 3, device=device)
    print(f"✅ Tensor created on device: {device}")

except ImportError as e:
    print(f"❌ PyTorch not installed: {e}")
    sys.exit(1)

# Check transformers
try:
    import transformers
    print(f"✅ Transformers version: {transformers.__version__}")
except ImportError as e:
    print(f"❌ Transformers not installed: {e}")
    sys.exit(1)

# Check sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    print(f"✅ Sentence-transformers imported successfully")

    # Try loading a small model
    print("\nTesting model loading (this may take a moment)...")
    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    model = SentenceTransformer(model_name)
    print(f"✅ Successfully loaded model: {model_name}")

    # Test encoding
    test_sentences = ["This is a test sentence.", "Another test sentence."]
    embeddings = model.encode(test_sentences)
    print(f"✅ Generated embeddings with shape: {embeddings.shape}")
    print(f"   Embedding dimension: {embeddings.shape[1]}")

    # Calculate similarity
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    print(f"✅ Cosine similarity between test sentences: {similarity:.4f}")

except ImportError as e:
    print(f"❌ Sentence-transformers not installed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during testing: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL VERIFICATIONS PASSED!")
print("="*60)
print("\nYou can now use sentence-transformers in your project.")
print("Example usage:")
print("  from sentence_transformers import SentenceTransformer")
print("  model = SentenceTransformer('all-MiniLM-L6-v2')")
print("  embeddings = model.encode(['Your text here'])")
EOF

print_step "Running verification..."
$VENV_PYTHON verify_sentence_transformers.py

VERIFICATION_RESULT=$?

# ============================================================================
# OPTIMIZATION TIPS
# ============================================================================

print_header "💡 OPTIMIZATION TIPS FOR MAC"

if [ "$IS_APPLE_SILICON" = true ]; then
    print_info "Apple Silicon Optimization Tips:"
    echo "  • PyTorch will automatically use Metal (MPS) for acceleration"
    echo "  • Set device='mps' in your code for GPU acceleration:"
    echo "    model = SentenceTransformer('model-name', device='mps')"
    echo "  • For debugging, use PYTORCH_ENABLE_MPS_FALLBACK=1"
    echo "  • Monitor GPU usage: sudo powermetrics --samplers gpu_power"
else
    print_info "Intel Mac Optimization Tips:"
    echo "  • PyTorch will use CPU optimizations"
    echo "  • Consider using smaller models for better performance"
    echo "  • Enable multi-threading: export OMP_NUM_THREADS=4"
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "📊 INSTALLATION SUMMARY"

if [ $VERIFICATION_RESULT -eq 0 ]; then
    print_status "Installation completed successfully!"
    echo ""
    echo "Installed packages:"
    echo "  ✅ PyTorch (with Metal support on Apple Silicon)"
    echo "  ✅ Transformers"
    echo "  ✅ Sentence-Transformers"
    echo "  ✅ Supporting libraries (scipy, scikit-learn, nltk)"
    echo ""
    echo "You can now use sentence-transformers in your project!"
    echo ""
    echo "Quick test command:"
    echo "  python -c \"from sentence_transformers import SentenceTransformer; print('Success!')\""
else
    print_error "Verification failed. Please check the error messages above."
    exit 1
fi

# Clean up
rm -f verify_sentence_transformers.py

print_info "Installation complete! 🎉"