#!/usr/bin/env python3
"""
AWS Account ID Finder
=====================
This script helps you find your AWS Account ID and other useful information
to configure your .env file.

Usage: python get_aws_account.py
"""

import sys
import os
import json
from datetime import datetime

# Color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {text}{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.NC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.NC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.NC}")


def check_aws_cli():
    """Check if AWS CLI is installed"""
    try:
        import subprocess
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print_success(f"AWS CLI found: {version}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False


def get_aws_info_boto3():
    """Get AWS account information using boto3"""
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError

        print_info("Getting AWS account information using boto3...")

        # Create STS client
        sts = boto3.client('sts')

        # Get caller identity
        response = sts.get_caller_identity()

        account_id = response['Account']
        user_arn = response['Arn']
        user_id = response['UserId']

        # Get region
        session = boto3.Session()
        region = session.region_name or 'not set'

        # Parse user type from ARN
        if ':assumed-role/' in user_arn:
            user_type = 'Assumed Role'
        elif ':user/' in user_arn:
            user_type = 'IAM User'
        elif ':root' in user_arn:
            user_type = 'Root User (⚠️ Not recommended!)'
        else:
            user_type = 'Unknown'

        return {
            'account_id': account_id,
            'region': region,
            'user_arn': user_arn,
            'user_id': user_id,
            'user_type': user_type,
            'method': 'boto3'
        }

    except ImportError:
        print_warning("boto3 not installed. Install with: pip install boto3")
        return None
    except NoCredentialsError:
        print_error("No AWS credentials found")
        return None
    except ClientError as e:
        print_error(f"AWS API error: {e}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None


def get_aws_info_cli():
    """Get AWS account information using AWS CLI"""
    try:
        import subprocess
        import json

        print_info("Getting AWS account information using AWS CLI...")

        # Get caller identity
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print_error(f"AWS CLI error: {result.stderr}")
            return None

        identity = json.loads(result.stdout)

        # Get current region
        region_result = subprocess.run(
            ['aws', 'configure', 'get', 'region'],
            capture_output=True,
            text=True
        )
        region = region_result.stdout.strip() if region_result.returncode == 0 else 'not set'

        # Parse user type from ARN
        user_arn = identity['Arn']
        if ':assumed-role/' in user_arn:
            user_type = 'Assumed Role'
        elif ':user/' in user_arn:
            user_type = 'IAM User'
        elif ':root' in user_arn:
            user_type = 'Root User (⚠️ Not recommended!)'
        else:
            user_type = 'Unknown'

        return {
            'account_id': identity['Account'],
            'region': region,
            'user_arn': user_arn,
            'user_id': identity['UserId'],
            'user_type': user_type,
            'method': 'AWS CLI'
        }

    except Exception as e:
        print_error(f"Failed to get AWS info via CLI: {e}")
        return None


def generate_bucket_name(account_id):
    """Generate a unique S3 bucket name"""
    import random
    import string

    # Generate random suffix
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    bucket_name = f"uci-research-poc-{account_id}-{random_suffix}"

    return bucket_name


def update_env_file(account_id, region, bucket_name):
    """Offer to update .env file with discovered values"""
    env_path = '.env'

    if not os.path.exists(env_path):
        print_warning(".env file not found")
        return

    print(f"\n{Colors.BOLD}Would you like to update your .env file?{Colors.NC}")
    print(f"This will update:")
    print(f"  • AWS_ACCOUNT_ID = {account_id}")
    print(f"  • AWS_REGION = {region}")
    print(f"  • S3_BUCKET_NAME = {bucket_name}")

    response = input(f"\nUpdate .env file? (yes/no): ").lower().strip()

    if response == 'yes':
        try:
            # Read current .env file
            with open(env_path, 'r') as f:
                lines = f.readlines()

            # Update specific lines
            updated_lines = []
            for line in lines:
                if line.startswith('AWS_ACCOUNT_ID='):
                    updated_lines.append(f'AWS_ACCOUNT_ID={account_id}\n')
                elif line.startswith('AWS_REGION='):
                    updated_lines.append(f'AWS_REGION={region}\n')
                elif line.startswith('S3_BUCKET_NAME='):
                    updated_lines.append(f'S3_BUCKET_NAME={bucket_name}\n')
                else:
                    updated_lines.append(line)

            # Write updated content
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)

            print_success(".env file updated successfully!")

        except Exception as e:
            print_error(f"Failed to update .env file: {e}")
    else:
        print_info("Skipping .env file update")


def main():
    """Main execution function"""
    print_header("AWS ACCOUNT INFORMATION FINDER")

    # Try to get AWS info
    info = None

    # Try boto3 first
    info = get_aws_info_boto3()

    # If boto3 fails, try AWS CLI
    if not info and check_aws_cli():
        info = get_aws_info_cli()

    if not info:
        print_error("Could not retrieve AWS account information")
        print("\n" + Colors.BOLD + "To fix this:" + Colors.NC)
        print("1. Install boto3: pip install boto3")
        print("2. Configure AWS credentials: aws configure")
        print("3. Or set environment variables:")
        print("   export AWS_ACCESS_KEY_ID=your_key")
        print("   export AWS_SECRET_ACCESS_KEY=your_secret")
        print("   export AWS_DEFAULT_REGION=us-west-2")
        sys.exit(1)

    # Display account information
    print_header("YOUR AWS ACCOUNT DETAILS")

    print(f"{Colors.BOLD}Account ID:{Colors.NC} {Colors.GREEN}{info['account_id']}{Colors.NC}")
    print(f"{Colors.BOLD}Region:{Colors.NC} {info['region']}")
    print(f"{Colors.BOLD}User Type:{Colors.NC} {info['user_type']}")
    print(f"{Colors.BOLD}User ARN:{Colors.NC} {info['user_arn']}")
    print(f"{Colors.BOLD}Retrieved via:{Colors.NC} {info['method']}")

    # Generate bucket name suggestion
    bucket_name = generate_bucket_name(info['account_id'])
    print(f"\n{Colors.BOLD}Suggested S3 Bucket Name:{Colors.NC}")
    print(f"  {Colors.CYAN}{bucket_name}{Colors.NC}")

    # Show .env update instructions
    print_header("UPDATE YOUR .ENV FILE")

    print("Add these values to your .env file:\n")
    print(f"{Colors.YELLOW}AWS_ACCOUNT_ID={info['account_id']}{Colors.NC}")
    print(f"{Colors.YELLOW}AWS_REGION={info['region']}{Colors.NC}")
    print(f"{Colors.YELLOW}S3_BUCKET_NAME={bucket_name}{Colors.NC}")

    # Offer to automatically update
    if os.path.exists('.env'):
        update_env_file(info['account_id'], info['region'], bucket_name)

    # Additional recommendations
    print_header("NEXT STEPS")

    print("1. ✅ Your AWS Account ID has been found")
    print(f"2. {'✅' if os.path.exists('.env') else '❌'} .env file exists")
    print("3. Run: python aws_infrastructure/iam_setup.py")
    print("4. Run: python aws_infrastructure/s3_setup.py")
    print("5. Run: python aws_infrastructure/cost_monitoring.py")

    # Cost warning
    if info['user_type'] == 'Root User (⚠️ Not recommended!)':
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  WARNING: You're using the root user!{Colors.NC}")
        print("   Create an IAM user for better security:")
        print("   https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started_create-admin-group.html")

    print(f"\n{Colors.GREEN}✅ Ready to proceed with AWS setup!{Colors.NC}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled by user{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.NC}")
        sys.exit(1)