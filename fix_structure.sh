#!/bin/bash

# ============================================================================
# Fix Duplicated Folder Structure Script
# ============================================================================
# This script consolidates the duplicated uci-research-intelligence folders
# Moving all files from the inner folder to the outer folder
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

# Define paths
OUTER_DIR="/Users/jordanmoreno/Desktop/UCIRAG/uci-research-intelligence"
INNER_DIR="${OUTER_DIR}/uci-research-intelligence"

# ============================================================================
# SAFETY CHECKS
# ============================================================================

print_header "FOLDER STRUCTURE FIX SCRIPT"

# Check if we're in the right location
if [ ! -d "$OUTER_DIR" ]; then
    print_error "Outer directory not found: $OUTER_DIR"
    exit 1
fi

if [ ! -d "$INNER_DIR" ]; then
    print_error "Inner directory not found: $INNER_DIR"
    print_info "The structure may already be fixed or paths are incorrect"
    exit 1
fi

# Change to outer directory
cd "$OUTER_DIR"
print_status "Working in: $OUTER_DIR"

# ============================================================================
# SHOW CURRENT STRUCTURE
# ============================================================================

print_header "CURRENT STRUCTURE ANALYSIS"

echo -e "${BOLD}Outer directory contents:${NC}"
ls -la "$OUTER_DIR" | head -20
echo ""

echo -e "${BOLD}Inner directory contents:${NC}"
ls -la "$INNER_DIR" | head -20
echo ""

# Count files and directories
INNER_FILE_COUNT=$(find "$INNER_DIR" -type f ! -path "*/\.*" | wc -l | tr -d ' ')
print_info "Found $INNER_FILE_COUNT files in inner directory"

# ============================================================================
# CONFIRMATION
# ============================================================================

print_header "PLANNED ACTIONS"

echo "This script will:"
echo "1. Move all Python files (*.py) from inner to outer directory"
echo "2. Move setup_environment.sh from inner to outer"
echo "3. Move verify_setup.py from inner to outer"
echo "4. Move requirements.txt from inner to outer"
echo "5. Move config/config.py from inner to outer config/"
echo "6. Move .gitignore, README.md, and .env files"
echo "7. Move all project directories (data_generation, aws_infrastructure, etc.)"
echo "8. Delete the empty inner directory"
echo "9. Make all .sh scripts executable"
echo ""
print_warning "The venv folder will NOT be touched"
echo ""

read -p "Do you want to proceed? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    print_info "Operation cancelled"
    exit 0
fi

# ============================================================================
# BACKUP REMINDER
# ============================================================================

print_warning "It's recommended to backup your work before proceeding!"
read -p "Have you backed up your work? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    print_info "Please backup your work first, then run this script again"
    exit 0
fi

# ============================================================================
# PERFORM MIGRATION
# ============================================================================

print_header "MIGRATING FILES"

# Function to safely move files
safe_move() {
    local source="$1"
    local dest="$2"
    local desc="$3"

    if [ -e "$source" ]; then
        if [ -e "$dest" ]; then
            print_warning "$desc already exists at destination. Skipping."
        else
            mv "$source" "$dest"
            print_status "Moved: $desc"
        fi
    else
        print_info "$desc not found in inner directory (may already be moved)"
    fi
}

# Function to safely move and merge directories
safe_move_dir() {
    local source="$1"
    local dest="$2"
    local desc="$3"

    if [ -d "$source" ]; then
        if [ -d "$dest" ]; then
            print_info "Merging $desc directory contents..."
            # Use rsync to merge directories
            rsync -av --remove-source-files "$source/" "$dest/"
            # Remove empty source directory
            find "$source" -type d -empty -delete 2>/dev/null || true
            print_status "Merged: $desc"
        else
            mv "$source" "$dest"
            print_status "Moved: $desc directory"
        fi
    else
        print_info "$desc directory not found (may already be moved)"
    fi
}

# 1. Move main Python files
safe_move "${INNER_DIR}/setup_environment.sh" "${OUTER_DIR}/setup_environment.sh" "setup_environment.sh"
safe_move "${INNER_DIR}/verify_setup.py" "${OUTER_DIR}/verify_setup.py" "verify_setup.py"
safe_move "${INNER_DIR}/requirements.txt" "${OUTER_DIR}/requirements.txt" "requirements.txt"

# 2. Move configuration files
safe_move "${INNER_DIR}/.gitignore" "${OUTER_DIR}/.gitignore" ".gitignore"
safe_move "${INNER_DIR}/README.md" "${OUTER_DIR}/README.md" "README.md"
safe_move "${INNER_DIR}/.env" "${OUTER_DIR}/.env" ".env"
safe_move "${INNER_DIR}/.env.example" "${OUTER_DIR}/.env.example" ".env.example"

# 3. Move project directories
DIRECTORIES=(
    "data_generation"
    "aws_infrastructure"
    "embeddings"
    "search"
    "rag_pipeline"
    "frontend"
    "config"
    "tests"
    "docs"
    "logs"
    "data"
)

for dir in "${DIRECTORIES[@]}"; do
    safe_move_dir "${INNER_DIR}/${dir}" "${OUTER_DIR}/${dir}" "$dir"
done

# 4. Move any remaining Python files in root
if ls "${INNER_DIR}"/*.py 1> /dev/null 2>&1; then
    for file in "${INNER_DIR}"/*.py; do
        filename=$(basename "$file")
        safe_move "$file" "${OUTER_DIR}/${filename}" "$filename"
    done
fi

# 5. Move any remaining .sh files in root
if ls "${INNER_DIR}"/*.sh 1> /dev/null 2>&1; then
    for file in "${INNER_DIR}"/*.sh; do
        filename=$(basename "$file")
        safe_move "$file" "${OUTER_DIR}/${filename}" "$filename"
    done
fi

# 6. Move any JSON configuration files
if ls "${INNER_DIR}"/*.json 1> /dev/null 2>&1; then
    for file in "${INNER_DIR}"/*.json; do
        filename=$(basename "$file")
        safe_move "$file" "${OUTER_DIR}/${filename}" "$filename"
    done
fi

# ============================================================================
# CLEANUP
# ============================================================================

print_header "CLEANUP"

# Check if inner directory is empty (except for hidden files)
REMAINING_FILES=$(find "$INNER_DIR" -type f ! -path "*/\.*" 2>/dev/null | wc -l | tr -d ' ')

if [ "$REMAINING_FILES" -eq 0 ]; then
    print_info "Inner directory is empty, removing it..."
    rm -rf "$INNER_DIR"
    print_status "Removed empty inner directory"
else
    print_warning "Inner directory still contains $REMAINING_FILES files"
    print_info "Listing remaining files:"
    find "$INNER_DIR" -type f ! -path "*/\.*" | head -20
    echo ""
    read -p "Do you want to remove the inner directory anyway? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        rm -rf "$INNER_DIR"
        print_status "Removed inner directory"
    else
        print_info "Inner directory kept"
    fi
fi

# ============================================================================
# SET PERMISSIONS
# ============================================================================

print_header "SETTING PERMISSIONS"

# Make all .sh scripts executable
for script in "$OUTER_DIR"/*.sh "$OUTER_DIR"/**/*.sh; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        print_status "Made executable: $(basename $script)"
    fi
done

# Make Python scripts in aws_infrastructure executable
if [ -d "${OUTER_DIR}/aws_infrastructure" ]; then
    for script in "${OUTER_DIR}/aws_infrastructure"/*.py; do
        if [ -f "$script" ]; then
            chmod +x "$script"
            print_status "Made executable: $(basename $script)"
        fi
    done
fi

# Make verify_setup.py executable
if [ -f "${OUTER_DIR}/verify_setup.py" ]; then
    chmod +x "${OUTER_DIR}/verify_setup.py"
    print_status "Made executable: verify_setup.py"
fi

# ============================================================================
# VERIFY FINAL STRUCTURE
# ============================================================================

print_header "FINAL STRUCTURE"

echo -e "${BOLD}Project root contents:${NC}"
echo ""

# Use tree if available, otherwise use ls
if command -v tree &> /dev/null; then
    tree -L 2 -I 'venv|__pycache__|*.pyc' "$OUTER_DIR"
else
    ls -la "$OUTER_DIR"
    echo ""
    echo -e "${BOLD}Project directories:${NC}"
    for dir in "${DIRECTORIES[@]}"; do
        if [ -d "${OUTER_DIR}/${dir}" ]; then
            echo "  ✓ ${dir}/"
            # Show a few files in each directory
            file_count=$(find "${OUTER_DIR}/${dir}" -maxdepth 1 -type f | wc -l | tr -d ' ')
            if [ "$file_count" -gt 0 ]; then
                echo "    ($file_count files)"
            fi
        else
            echo "  ✗ ${dir}/ (missing)"
        fi
    done
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "✨ CONSOLIDATION COMPLETE"

print_success "Folder structure has been consolidated!"
echo ""
echo "Project location: ${OUTER_DIR}"
echo ""
echo -e "${BOLD}Key files in place:${NC}"

# Check for key files
KEY_FILES=(
    "setup_environment.sh"
    "verify_setup.py"
    "requirements.txt"
    ".gitignore"
    "README.md"
    "config/config.py"
)

for file in "${KEY_FILES[@]}"; do
    if [ -f "${OUTER_DIR}/${file}" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
    fi
done

echo ""
print_info "Next steps:"
echo "  1. cd ${OUTER_DIR}"
echo "  2. ./setup_environment.sh  (to set up Python environment)"
echo "  3. python verify_setup.py  (to verify everything is working)"
echo ""
print_success "All done! Your project structure is now clean and organized."