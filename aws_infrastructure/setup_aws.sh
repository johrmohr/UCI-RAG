#!/bin/bash

# UCI Research Intelligence - AWS CLI Setup Script for macOS
# This script helps set up AWS CLI and boto3 configuration on Mac systems
# Author: UCI Research Intelligence Team
# Date: 2025-01-21

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script is designed for macOS only."
        print_info "Detected OS: $OSTYPE"
        exit 1
    fi
    print_status "macOS detected: $(sw_vers -productVersion)"
}

# Function to check if Homebrew is installed
check_homebrew() {
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew is not installed."
        print_info "To install Homebrew, run:"
        echo ""
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        echo ""
        read -p "Would you like to install Homebrew now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            print_status "Homebrew installed successfully"
        else
            print_error "Homebrew is required to continue. Please install it and run this script again."
            exit 1
        fi
    else
        print_status "Homebrew is installed: $(brew --version | head -n 1)"
    fi
}

# Function to check and install AWS CLI
install_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI is not installed."
        print_info "Installing AWS CLI via Homebrew..."

        # Update Homebrew
        brew update

        # Install AWS CLI
        if brew install awscli; then
            print_status "AWS CLI installed successfully"
        else
            print_error "Failed to install AWS CLI"
            print_info "Try manual installation: brew install awscli"
            exit 1
        fi
    else
        print_status "AWS CLI is installed: $(aws --version 2>&1)"

        # Check for updates
        print_info "Checking for AWS CLI updates..."
        brew upgrade awscli 2>/dev/null || print_info "AWS CLI is up to date"
    fi
}

# Function to configure AWS credentials
configure_aws() {
    print_info "Setting up AWS credentials..."
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "                    AWS CONFIGURATION GUIDE                  "
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "You will need the following information:"
    echo ""
    echo "1. AWS Access Key ID"
    echo "   Format: AKIAIOSFODNN7EXAMPLE"
    echo "   Where to find: AWS Console → IAM → Users → Security credentials"
    echo ""
    echo "2. AWS Secret Access Key"
    echo "   Format: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    echo "   Where to find: Only shown when creating a new access key"
    echo ""
    echo "3. Default region name"
    echo "   Recommended: us-west-2 (Oregon) or us-east-1 (N. Virginia)"
    echo "   Full list: https://docs.aws.amazon.com/general/latest/gr/rande.html"
    echo ""
    echo "4. Default output format"
    echo "   Options: json, yaml, text, table"
    echo "   Recommended: json"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    read -p "Press Enter when you're ready to configure AWS CLI..."

    # Check if credentials already exist
    if [[ -f ~/.aws/credentials ]]; then
        print_warning "AWS credentials already exist at ~/.aws/credentials"
        read -p "Do you want to reconfigure? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping AWS configuration"
            return
        fi
    fi

    # Run AWS configure
    aws configure

    print_status "AWS CLI configuration complete"
}

# Function to create verification script
create_verification_script() {
    print_info "Creating AWS verification script..."

    cat > "$SCRIPT_DIR/verify_aws_connection.py" << 'EOF'
#!/usr/bin/env python3
"""
AWS Connection Verification Script
Tests AWS credentials and basic service connectivity
"""

import sys
import json
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
except ImportError:
    print("Error: boto3 is not installed. Please run: pip install boto3")
    sys.exit(1)

def verify_credentials():
    """Verify AWS credentials are configured correctly"""
    print("\n" + "="*60)
    print("AWS CREDENTIAL VERIFICATION")
    print("="*60 + "\n")

    try:
        # Create STS client to verify credentials
        sts = boto3.client('sts')

        # Get caller identity
        identity = sts.get_caller_identity()

        print("✅ AWS Credentials Valid!")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")

        return True

    except NoCredentialsError:
        print("❌ No AWS credentials found!")
        print("   Please run: aws configure")
        return False

    except PartialCredentialsError:
        print("❌ Incomplete AWS credentials!")
        print("   Please check your ~/.aws/credentials file")
        return False

    except ClientError as e:
        print(f"❌ AWS API Error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_service_access():
    """Test access to common AWS services"""
    print("\n" + "="*60)
    print("SERVICE ACCESS TEST")
    print("="*60 + "\n")

    services_to_test = [
        ('s3', 'list_buckets', {}),
        ('ec2', 'describe_regions', {}),
        ('lambda', 'list_functions', {'MaxItems': 1}),
        ('dynamodb', 'list_tables', {'Limit': 1})
    ]

    results = []

    for service_name, operation, params in services_to_test:
        try:
            client = boto3.client(service_name)
            method = getattr(client, operation)
            method(**params)
            print(f"✅ {service_name.upper()}: Access verified")
            results.append((service_name, True))
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                print(f"⚠️  {service_name.upper()}: No permissions (this is OK if not using this service)")
            else:
                print(f"❌ {service_name.upper()}: {error_code}")
            results.append((service_name, False))
        except Exception as e:
            print(f"❌ {service_name.upper()}: {str(e)}")
            results.append((service_name, False))

    return results

def check_region_config():
    """Check configured AWS region"""
    print("\n" + "="*60)
    print("REGION CONFIGURATION")
    print("="*60 + "\n")

    session = boto3.Session()
    region = session.region_name

    if region:
        print(f"✅ Default Region: {region}")

        # List available regions
        ec2 = boto3.client('ec2', region_name='us-east-1')
        try:
            regions = ec2.describe_regions()['Regions']
            region_names = [r['RegionName'] for r in regions]

            if region in region_names:
                print(f"   Region is valid and available")
            else:
                print(f"   ⚠️  Warning: Region may not be valid")

        except Exception:
            print("   Could not verify region validity")
    else:
        print("⚠️  No default region configured")
        print("   Run 'aws configure' to set a default region")

    return region

def save_report(identity, region, service_results):
    """Save verification report to file"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'credentials_valid': identity is not None,
        'identity': identity,
        'region': region,
        'service_access': {service: status for service, status in service_results}
    }

    filename = f"aws_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Report saved to: {filename}")

def main():
    print("\n" + "🔍 Starting AWS Configuration Verification...\n")

    # Verify credentials
    creds_valid = verify_credentials()

    if not creds_valid:
        print("\n❌ Verification failed. Please configure AWS credentials first.")
        sys.exit(1)

    # Check region
    region = check_region_config()

    # Test service access
    service_results = test_service_access()

    # Get identity for report
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
    except:
        identity = None

    # Save report
    save_report(identity, region, service_results)

    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("="*60)

    if all(status for _, status in service_results):
        print("\nAll services accessible! Your AWS setup is fully configured.")
    else:
        print("\nSome services are not accessible. This is normal if you don't have")
        print("permissions for those services. Check the report for details.")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$SCRIPT_DIR/verify_aws_connection.py"
    print_status "Verification script created: verify_aws_connection.py"
}

# Function to create boto3 configuration
create_boto3_config() {
    print_info "Creating boto3 configuration file..."

    cat > "$SCRIPT_DIR/boto3_config.py" << 'EOF'
"""
Boto3 Configuration for UCI Research Intelligence System
This module provides centralized AWS configuration for the project
"""

import os
import boto3
from botocore.config import Config
from typing import Optional, Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class AWSConfig:
    """Centralized AWS configuration management"""

    def __init__(self):
        """Initialize AWS configuration from environment variables"""
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
        self.aws_profile = os.getenv('AWS_PROFILE', 'default')

        # Custom configuration for different services
        self.service_configs = {
            's3': {
                'signature_version': 's3v4',
                'max_pool_connections': 50
            },
            'lambda': {
                'read_timeout': 300,
                'max_pool_connections': 10
            },
            'dynamodb': {
                'max_pool_connections': 25
            }
        }

        # Default retry configuration
        self.retry_config = {
            'max_attempts': 3,
            'mode': 'adaptive'
        }

    def get_session(self, profile_name: Optional[str] = None) -> boto3.Session:
        """
        Create a boto3 session with configured credentials

        Args:
            profile_name: Optional AWS profile name to use

        Returns:
            boto3.Session: Configured AWS session
        """
        profile = profile_name or self.aws_profile

        if self.aws_access_key_id and self.aws_secret_access_key:
            # Use explicit credentials if available
            return boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
        else:
            # Fall back to profile-based authentication
            return boto3.Session(
                profile_name=profile,
                region_name=self.aws_region
            )

    def get_client(self,
                   service_name: str,
                   custom_config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a boto3 client for a specific AWS service

        Args:
            service_name: Name of the AWS service (e.g., 's3', 'lambda')
            custom_config: Optional custom configuration dictionary

        Returns:
            boto3 client for the specified service
        """
        session = self.get_session()

        # Merge service-specific config with custom config
        config_dict = {
            'region_name': self.aws_region,
            'retries': self.retry_config
        }

        if service_name in self.service_configs:
            config_dict.update(self.service_configs[service_name])

        if custom_config:
            config_dict.update(custom_config)

        config = Config(**config_dict)

        return session.client(service_name, config=config)

    def get_resource(self,
                     service_name: str,
                     custom_config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a boto3 resource for a specific AWS service

        Args:
            service_name: Name of the AWS service (e.g., 's3', 'dynamodb')
            custom_config: Optional custom configuration dictionary

        Returns:
            boto3 resource for the specified service
        """
        session = self.get_session()

        # Merge service-specific config with custom config
        config_dict = {
            'region_name': self.aws_region,
            'retries': self.retry_config
        }

        if service_name in self.service_configs:
            config_dict.update(self.service_configs[service_name])

        if custom_config:
            config_dict.update(custom_config)

        config = Config(**config_dict)

        return session.resource(service_name, config=config)

    def validate_credentials(self) -> bool:
        """
        Validate AWS credentials by attempting to get caller identity

        Returns:
            bool: True if credentials are valid, False otherwise
        """
        try:
            sts_client = self.get_client('sts')
            sts_client.get_caller_identity()
            return True
        except Exception as e:
            print(f"Credential validation failed: {e}")
            return False

# Singleton instance
aws_config = AWSConfig()

# Convenience functions
def get_s3_client():
    """Get configured S3 client"""
    return aws_config.get_client('s3')

def get_dynamodb_resource():
    """Get configured DynamoDB resource"""
    return aws_config.get_resource('dynamodb')

def get_lambda_client():
    """Get configured Lambda client"""
    return aws_config.get_client('lambda')

def get_bedrock_client():
    """Get configured Bedrock client for AI/ML services"""
    return aws_config.get_client('bedrock-runtime')

# Example usage
if __name__ == "__main__":
    # Test configuration
    config = AWSConfig()

    print("Testing AWS Configuration...")
    if config.validate_credentials():
        print("✅ AWS credentials are valid")
        print(f"   Region: {config.aws_region}")
        print(f"   Profile: {config.aws_profile}")
    else:
        print("❌ AWS credentials validation failed")
        print("   Please check your configuration")
EOF

    print_status "Boto3 configuration created: boto3_config.py"
}

# Function to create .env template
create_env_template() {
    print_info "Creating .env template file..."

    cat > "$PROJECT_ROOT/.env.example" << 'EOF'
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-west-2
AWS_PROFILE=default

# S3 Buckets
S3_DATA_BUCKET=uci-research-data
S3_EMBEDDINGS_BUCKET=uci-research-embeddings
S3_MODELS_BUCKET=uci-research-models

# DynamoDB Tables
DYNAMODB_METADATA_TABLE=uci-research-metadata
DYNAMODB_USERS_TABLE=uci-research-users

# Lambda Functions
LAMBDA_EMBEDDING_FUNCTION=uci-generate-embeddings
LAMBDA_SEARCH_FUNCTION=uci-search-handler

# API Configuration
API_GATEWAY_URL=https://api.example.com
API_KEY=your_api_key_here

# OpenAI Configuration (for RAG)
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8000
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-west1-gcp

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/uci_research

# Security
JWT_SECRET_KEY=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here
EOF

    print_status ".env template created: .env.example"
}

# Main execution
main() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "     UCI Research Intelligence - AWS Setup Script for macOS   "
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Get script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    # Step 1: Check macOS
    check_macos

    # Step 2: Check and install Homebrew
    check_homebrew

    # Step 3: Install AWS CLI
    install_aws_cli

    # Step 4: Configure AWS
    configure_aws

    # Step 5: Create verification script
    create_verification_script

    # Step 6: Create boto3 configuration
    create_boto3_config

    # Step 7: Create .env template
    create_env_template

    # Final steps
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "                    SETUP COMPLETE!                           "
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_status "AWS CLI setup completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Verify your AWS connection:"
    echo "   python3 $SCRIPT_DIR/verify_aws_connection.py"
    echo ""
    echo "2. Copy and configure the .env file:"
    echo "   cp $PROJECT_ROOT/.env.example $PROJECT_ROOT/.env"
    echo "   # Then edit .env with your actual values"
    echo ""
    echo "3. Install Python dependencies:"
    echo "   pip install -r $PROJECT_ROOT/requirements.txt"
    echo ""
    echo "4. Test boto3 configuration:"
    echo "   python3 $SCRIPT_DIR/boto3_config.py"
    echo ""
    echo "📚 Additional Resources:"
    echo "   • AWS CLI Documentation: https://docs.aws.amazon.com/cli/"
    echo "   • Boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/"
    echo "   • IAM Best Practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html"
    echo ""
}

# Error handler
trap 'print_error "Script failed at line $LINENO"' ERR

# Run main function
main