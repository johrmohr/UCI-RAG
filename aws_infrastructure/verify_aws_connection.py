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
