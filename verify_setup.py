#!/usr/bin/env python3
"""
UCI Research Intelligence - Setup Verification Script
======================================================
Comprehensive verification of your development environment and AWS setup.
Provides a friendly checklist with clear next steps for any issues.

Usage: python verify_setup.py
"""

import os
import sys
import json
import importlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import subprocess

# ============================================================================
# TERMINAL COLORS AND EMOJIS
# ============================================================================

class Colors:
    """Terminal color codes for pretty output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class Emoji:
    """Emoji indicators for status"""
    SUCCESS = "✅"
    FAILURE = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    WORKING = "🔄"
    MONEY = "💵"
    ROCKET = "🚀"
    PACKAGE = "📦"
    CLOUD = "☁️"
    KEY = "🔑"
    SEARCH = "🔍"
    AI = "🤖"
    FOLDER = "📁"
    CHECK = "✓"
    CROSS = "✗"
    ARROW = "→"
    SPARKLE = "✨"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {text}{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.NC}\n")


def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}{text}{Colors.NC}")
    print(f"{Colors.MAGENTA}{'─'*50}{Colors.NC}")


def print_success(text: str, detail: str = ""):
    """Print success message"""
    if detail:
        print(f"{Emoji.SUCCESS} {Colors.GREEN}{text}{Colors.NC} - {detail}")
    else:
        print(f"{Emoji.SUCCESS} {Colors.GREEN}{text}{Colors.NC}")


def print_failure(text: str, detail: str = ""):
    """Print failure message"""
    if detail:
        print(f"{Emoji.FAILURE} {Colors.RED}{text}{Colors.NC} - {detail}")
    else:
        print(f"{Emoji.FAILURE} {Colors.RED}{text}{Colors.NC}")


def print_warning(text: str, detail: str = ""):
    """Print warning message"""
    if detail:
        print(f"{Emoji.WARNING} {Colors.YELLOW}{text}{Colors.NC} - {detail}")
    else:
        print(f"{Emoji.WARNING} {Colors.YELLOW}{text}{Colors.NC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Emoji.INFO} {Colors.BLUE}{text}{Colors.NC}")


def print_next_step(text: str):
    """Print next step instruction"""
    print(f"   {Emoji.ARROW} {Colors.YELLOW}{text}{Colors.NC}")


# ============================================================================
# VERIFICATION CLASSES
# ============================================================================

class SetupVerifier:
    """Main verification class"""

    def __init__(self):
        self.results = {
            'python': {'status': False, 'details': ''},
            'packages': {'status': False, 'details': [], 'missing': []},
            'aws_credentials': {'status': False, 'details': ''},
            's3_access': {'status': False, 'details': '', 'buckets': []},
            'opensearch': {'status': 'pending', 'details': 'Not set up yet'},
            'bedrock': {'status': False, 'details': ''},
            'env_file': {'status': False, 'details': ''},
            'project_structure': {'status': False, 'details': ''},
        }
        self.boto3_available = False
        self.project_root = Path(__file__).parent

    def run_all_checks(self):
        """Run all verification checks"""
        print_header("🚀 UCI RESEARCH INTELLIGENCE - SETUP VERIFICATION")
        print(f"Verification started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run checks
        self.check_python_version()
        self.check_project_structure()
        self.check_env_file()
        self.check_packages()

        # Only run AWS checks if boto3 is available
        if self.boto3_available:
            self.check_aws_credentials()
            if self.results['aws_credentials']['status']:
                self.check_s3_access()
                self.check_opensearch_availability()
                self.check_bedrock_availability()
        else:
            print_warning("Skipping AWS checks - boto3 not installed")

        # Print summary
        self.print_summary()
        self.print_next_steps()

    def check_python_version(self):
        """Check Python version"""
        print_section(f"{Emoji.PACKAGE} Python Version Check")

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if version.major == 3 and version.minor >= 9:
            self.results['python']['status'] = True
            self.results['python']['details'] = version_str
            print_success(f"Python {version_str}", "Meets requirement (3.9+)")
        else:
            self.results['python']['status'] = False
            self.results['python']['details'] = version_str
            print_failure(f"Python {version_str}", "Requires Python 3.9+")

    def check_project_structure(self):
        """Check if project directories exist"""
        print_section(f"{Emoji.FOLDER} Project Structure Check")

        required_dirs = [
            'data_generation',
            'aws_infrastructure',
            'embeddings',
            'search',
            'rag_pipeline',
            'frontend',
            'config',
            'tests',
            'docs'
        ]

        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            self.results['project_structure']['status'] = False
            self.results['project_structure']['details'] = f"Missing: {', '.join(missing_dirs)}"
            print_failure("Project structure incomplete", f"Missing {len(missing_dirs)} directories")
        else:
            self.results['project_structure']['status'] = True
            self.results['project_structure']['details'] = "All directories present"
            print_success("All project directories present")

    def check_env_file(self):
        """Check if .env file exists"""
        print_section(f"{Emoji.KEY} Environment File Check")

        env_path = self.project_root / '.env'
        env_example_path = self.project_root / '.env.example'

        if env_path.exists():
            self.results['env_file']['status'] = True
            self.results['env_file']['details'] = "Found"
            print_success(".env file exists")

            # Check if key variables are set
            from dotenv import dotenv_values
            env_vars = dotenv_values(env_path)

            important_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']
            missing_vars = [var for var in important_vars if not env_vars.get(var) or env_vars.get(var).startswith('your_')]

            if missing_vars:
                print_warning("Some environment variables not configured", f"Missing: {', '.join(missing_vars)}")
        else:
            self.results['env_file']['status'] = False
            self.results['env_file']['details'] = "Not found"
            print_failure(".env file not found")

            if env_example_path.exists():
                print_info(".env.example exists - copy it to .env and update values")

    def check_packages(self):
        """Check if required Python packages are installed"""
        print_section(f"{Emoji.PACKAGE} Python Package Check")

        critical_packages = {
            'boto3': 'AWS SDK',
            'pandas': 'Data Processing',
            'numpy': 'Numerical Computing',
            'faker': 'Data Generation',
            'langchain': 'RAG Framework',
            'streamlit': 'Web Interface',
            'dotenv': 'Environment Variables',
            'opensearchpy': 'OpenSearch Client',
            'sentence_transformers': 'Embeddings',
        }

        installed = []
        missing = []

        for package, description in critical_packages.items():
            try:
                if package == 'opensearchpy':
                    importlib.import_module('opensearchpy')
                elif package == 'dotenv':
                    importlib.import_module('dotenv')
                else:
                    importlib.import_module(package)
                installed.append(f"{description} ({package})")
                if package == 'boto3':
                    self.boto3_available = True
            except ImportError:
                missing.append(f"{description} ({package})")

        self.results['packages']['details'] = installed
        self.results['packages']['missing'] = missing

        if missing:
            self.results['packages']['status'] = False
            print_failure(f"{len(installed)}/{len(critical_packages)} packages installed")
            for pkg in missing:
                print(f"   {Emoji.CROSS} {Colors.RED}Missing: {pkg}{Colors.NC}")
        else:
            self.results['packages']['status'] = True
            print_success(f"All {len(critical_packages)} critical packages installed")

    def check_aws_credentials(self):
        """Check if AWS credentials are configured"""
        print_section(f"{Emoji.CLOUD} AWS Credentials Check")

        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError

            # Try to get caller identity
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()

            self.results['aws_credentials']['status'] = True
            self.results['aws_credentials']['details'] = identity['Account']
            print_success("AWS credentials configured", f"Account: {identity['Account']}")
            print_info(f"User ARN: {identity['Arn']}")

            # Check region
            session = boto3.Session()
            region = session.region_name or 'Not set'
            print_info(f"Default Region: {region}")

        except NoCredentialsError:
            self.results['aws_credentials']['status'] = False
            self.results['aws_credentials']['details'] = "No credentials"
            print_failure("AWS credentials not found")

        except ClientError as e:
            self.results['aws_credentials']['status'] = False
            self.results['aws_credentials']['details'] = str(e)
            print_failure("AWS credentials invalid", str(e))

        except Exception as e:
            self.results['aws_credentials']['status'] = False
            self.results['aws_credentials']['details'] = str(e)
            print_failure("Failed to verify AWS credentials", str(e))

    def check_s3_access(self):
        """Check S3 access and list buckets"""
        print_section(f"{Emoji.FOLDER} S3 Access Check")

        try:
            import boto3
            from botocore.exceptions import ClientError

            s3 = boto3.client('s3')

            # List buckets
            response = s3.list_buckets()
            buckets = response.get('Buckets', [])

            self.results['s3_access']['status'] = True
            self.results['s3_access']['buckets'] = [b['Name'] for b in buckets]

            if buckets:
                print_success(f"S3 access verified - {len(buckets)} bucket(s) found")
                for bucket in buckets[:5]:  # Show first 5 buckets
                    print(f"   {Emoji.CHECK} {bucket['Name']}")
                if len(buckets) > 5:
                    print(f"   ... and {len(buckets) - 5} more")

                # Look for UCI research bucket
                uci_buckets = [b['Name'] for b in buckets if 'uci' in b['Name'].lower() or 'research' in b['Name'].lower()]
                if uci_buckets:
                    print_info(f"Found UCI Research bucket: {uci_buckets[0]}")
            else:
                print_warning("S3 access works but no buckets found")
                self.results['s3_access']['details'] = "No buckets"

        except ClientError as e:
            self.results['s3_access']['status'] = False
            self.results['s3_access']['details'] = str(e)
            print_failure("S3 access failed", e.response['Error']['Code'])

        except Exception as e:
            self.results['s3_access']['status'] = False
            self.results['s3_access']['details'] = str(e)
            print_failure("S3 check failed", str(e))

    def check_opensearch_availability(self):
        """Check if OpenSearch service is available in the region"""
        print_section(f"{Emoji.SEARCH} OpenSearch Service Check")

        try:
            import boto3
            from botocore.exceptions import ClientError

            # Use us-west-2 as default if not set
            session = boto3.Session()
            region = session.region_name or 'us-west-2'

            es = boto3.client('es', region_name=region)

            # Try to list domains (won't return any if none exist, but verifies service access)
            response = es.list_domain_names()
            domains = response.get('DomainNames', [])

            # Mark OpenSearch as pending setup rather than failed
            self.results['opensearch']['status'] = 'pending'
            print_info(f"OpenSearch service available in {region}")

            if domains:
                print_info(f"Found {len(domains)} existing domain(s)")
                for domain in domains[:3]:
                    print(f"   {Emoji.CHECK} {domain['DomainName']}")
                self.results['opensearch']['details'] = f"{len(domains)} domains exist"
            else:
                print_info("No OpenSearch domains created yet - this is expected for initial setup")
                self.results['opensearch']['details'] = "Not set up yet"

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                self.results['opensearch']['status'] = 'pending'
                self.results['opensearch']['details'] = "Will need permissions when setting up"
                print_info("OpenSearch will require additional permissions when you set it up")
            else:
                self.results['opensearch']['status'] = 'pending'
                self.results['opensearch']['details'] = "Not set up yet"
                print_info("OpenSearch not configured yet - this is normal for POC")

        except Exception as e:
            self.results['opensearch']['status'] = 'pending'
            self.results['opensearch']['details'] = "Not set up yet"
            print_info("OpenSearch not configured - will set up later if needed")

    def check_bedrock_availability(self):
        """Check if Bedrock service is available in the region"""
        print_section(f"{Emoji.AI} AWS Bedrock Check")

        try:
            import boto3
            from botocore.exceptions import ClientError

            # Bedrock is available in limited regions
            session = boto3.Session()
            region = session.region_name or 'us-west-2'

            # List of regions where Bedrock is available (as of 2024)
            bedrock_regions = ['us-east-1', 'us-west-2', 'ap-southeast-1', 'ap-northeast-1', 'eu-central-1']

            if region not in bedrock_regions:
                print_warning(f"Bedrock not available in {region}")
                print_info(f"Available regions: {', '.join(bedrock_regions)}")
                self.results['bedrock']['status'] = False
                self.results['bedrock']['details'] = f"Not in {region}"
                return

            bedrock = boto3.client('bedrock', region_name=region)

            # Try to list foundation models
            response = bedrock.list_foundation_models()
            models = response.get('modelSummaries', [])

            self.results['bedrock']['status'] = True
            print_success(f"Bedrock service available in {region}")

            # Show available models
            if models:
                print_info(f"Found {len(models)} available models")
                # Show a few model examples
                claude_models = [m for m in models if 'claude' in m['modelId'].lower()]
                if claude_models:
                    print(f"   {Emoji.CHECK} Claude models available: {len(claude_models)}")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                self.results['bedrock']['status'] = False
                self.results['bedrock']['details'] = "No permissions"
                print_warning("Bedrock service exists but no permissions")
            else:
                self.results['bedrock']['status'] = False
                self.results['bedrock']['details'] = error_code
                print_failure("Bedrock service check failed", error_code)

        except Exception as e:
            # Bedrock client might not exist in older boto3 versions
            self.results['bedrock']['status'] = False
            self.results['bedrock']['details'] = "Not available"
            print_warning("Bedrock not available", "Update boto3 or check region")


    def print_summary(self):
        """Print a summary checklist"""
        print_header(f"{Emoji.SPARKLE} VERIFICATION SUMMARY")

        # Print checklist
        print(f"{Colors.BOLD}Setup Checklist:{Colors.NC}\n")

        checklist = [
            ('Python 3.9+', self.results['python']['status'], self.results['python']['details']),
            ('Project Structure', self.results['project_structure']['status'], self.results['project_structure']['details']),
            ('Environment File', self.results['env_file']['status'], self.results['env_file']['details']),
            ('Python Packages', self.results['packages']['status'],
             f"{len(self.results['packages']['details'])} installed, {len(self.results['packages']['missing'])} missing"),
            ('AWS Credentials', self.results['aws_credentials']['status'], self.results['aws_credentials']['details']),
            ('S3 Access', self.results['s3_access']['status'],
             f"{len(self.results['s3_access']['buckets'])} buckets" if self.results['s3_access']['status'] else "Not verified"),
            ('Bedrock Service', self.results['bedrock']['status'], self.results['bedrock']['details']),
            ('OpenSearch Service', self.results['opensearch']['status'], self.results['opensearch']['details']),
        ]

        for item, status, detail in checklist:
            if status == True:
                print(f"  {Emoji.SUCCESS} {Colors.GREEN}{item:20}{Colors.NC} {detail}")
            elif status == 'pending':
                print(f"  {Emoji.INFO} {Colors.BLUE}{item:20}{Colors.NC} {detail}")
            else:
                print(f"  {Emoji.FAILURE} {Colors.RED}{item:20}{Colors.NC} {detail}")

        # Calculate core services status (excluding OpenSearch which is optional for POC)
        core_ready = (
            self.results['python']['status'] and
            self.results['project_structure']['status'] and
            self.results['env_file']['status'] and
            len(self.results['packages']['missing']) == 0 and
            self.results['aws_credentials']['status']
        )

        # Overall status
        print(f"\n{Colors.BOLD}POC Status:{Colors.NC}")

        if core_ready:
            print(f"\n{Emoji.ROCKET} {Colors.GREEN}{Colors.BOLD}Ready for Data Generation!{Colors.NC}")
            print(f"{Colors.GREEN}Core services are configured. You can start generating and processing data.{Colors.NC}")
            if not self.results['s3_access']['status']:
                print(f"{Colors.YELLOW}Note: Run s3_setup.py to create your S3 bucket when ready.{Colors.NC}")
            if self.results['opensearch']['status'] == 'pending':
                print(f"{Colors.BLUE}Note: OpenSearch can be set up later when needed for vector search.{Colors.NC}")
        else:
            missing_items = []
            if not self.results['python']['status']:
                missing_items.append("Python 3.9+")
            if not self.results['project_structure']['status']:
                missing_items.append("Project structure")
            if not self.results['env_file']['status']:
                missing_items.append("Environment file")
            if len(self.results['packages']['missing']) > 0:
                missing_items.append("Python packages")
            if not self.results['aws_credentials']['status']:
                missing_items.append("AWS credentials")

            print(f"\n{Emoji.WARNING} {Colors.YELLOW}{Colors.BOLD}Setup Incomplete{Colors.NC}")
            print(f"Missing: {', '.join(missing_items)}")

    def print_next_steps(self):
        """Print next steps based on failures"""
        print_header(f"{Emoji.ARROW} NEXT STEPS")

        has_issues = False

        # Python version
        if not self.results['python']['status']:
            has_issues = True
            print(f"{Colors.BOLD}Fix Python Version:{Colors.NC}")
            print_next_step("Install Python 3.9+: brew install python@3.9")
            print()

        # Project structure
        if not self.results['project_structure']['status']:
            has_issues = True
            print(f"{Colors.BOLD}Fix Project Structure:{Colors.NC}")
            print_next_step("Run from project root: cd uci-research-intelligence")
            print()

        # Environment file
        if not self.results['env_file']['status']:
            has_issues = True
            print(f"{Colors.BOLD}Create Environment File:{Colors.NC}")
            print_next_step("You already have a .env file - check if variables are set")
            print_next_step("Run: python get_aws_account.py")
            print_next_step("Update AWS credentials in .env")
            print()

        # Missing packages
        if self.results['packages']['missing']:
            has_issues = True
            print(f"{Colors.BOLD}Install Missing Packages:{Colors.NC}")
            print_next_step("Run: pip install -r requirements.txt")
            print_next_step("Or use setup script: ./setup_environment.sh")
            print_next_step("For sentence-transformers: ./install_missing.sh")
            print()

        # AWS credentials
        if not self.results['aws_credentials']['status']:
            has_issues = True
            print(f"{Colors.BOLD}Configure AWS Credentials:{Colors.NC}")
            print_next_step("Run: aws configure")
            print_next_step("Or run: ./aws_infrastructure/setup_aws.sh")
            print()

        # S3 setup
        if self.results['aws_credentials']['status'] and not self.results['s3_access']['buckets']:
            print(f"{Colors.BOLD}When Ready - Create S3 Bucket:{Colors.NC}")
            print_next_step("Run: python aws_infrastructure/s3_setup.py")
            print()

        # OpenSearch (optional)
        if self.results['opensearch']['status'] == 'pending':
            print(f"{Colors.BOLD}Optional - OpenSearch Setup:{Colors.NC}")
            print_next_step("OpenSearch can be configured later for vector search")
            print_next_step("For now, you can use local ChromaDB or Pinecone")
            print()

        if not has_issues:
            print(f"{Emoji.ROCKET} {Colors.GREEN}Ready to start developing!{Colors.NC}\n")
            print(f"{Colors.BOLD}Suggested workflow:{Colors.NC}")
            print_next_step("1. Generate test data: python data_generation/generate_test_data.py")
            print_next_step("2. Create embeddings: python embeddings/create_embeddings.py")
            print_next_step("3. Test RAG pipeline: python rag_pipeline/test_rag.py")
            print_next_step("4. Launch UI: streamlit run frontend/app.py")

        print()
        print(f"{Colors.CYAN}Project Resources:{Colors.NC}")
        print(f"  • Configuration: {Colors.BOLD}config/config.py{Colors.NC}")
        print(f"  • Documentation: {Colors.BOLD}docs/README.md{Colors.NC}")
        print(f"  • AWS Setup: {Colors.BOLD}aws_infrastructure/{Colors.NC}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    try:
        verifier = SetupVerifier()
        verifier.run_all_checks()
    except KeyboardInterrupt:
        print(f"\n{Emoji.WARNING} Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Emoji.FAILURE} {Colors.RED}Unexpected error: {e}{Colors.NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()