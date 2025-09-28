#!/usr/bin/env python3
"""
S3 Setup Script for UCI Research Intelligence POC
Creates and configures S3 bucket with cost optimization and security best practices
"""

import json
import sys
import time
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import random
import string

class S3Setup:
    """Manages S3 bucket creation and configuration for UCI Research Intelligence"""

    def __init__(self, project_prefix: str = "uci-research-poc"):
        """
        Initialize S3 setup

        Args:
            project_prefix: Prefix for bucket naming
        """
        self.project_prefix = project_prefix

        try:
            self.s3_client = boto3.client('s3')
            self.s3_resource = boto3.resource('s3')
            self.sts = boto3.client('sts')
            self.account_id = self.sts.get_caller_identity()['Account']
            self.region = boto3.Session().region_name or 'us-west-2'

            print(f"✅ Connected to AWS Account: {self.account_id}")
            print(f"   Region: {self.region}")

        except NoCredentialsError:
            print("❌ No AWS credentials found. Please run 'aws configure' first.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to connect to AWS: {e}")
            sys.exit(1)

        # Generate unique bucket name (S3 bucket names must be globally unique)
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.bucket_name = f"{self.project_prefix}-{self.account_id}-{random_suffix}"

        # Folder structure for organization
        self.folders = [
            'raw-data/',
            'embeddings/',
            'metadata/',
            'logs/'
        ]

    def create_bucket(self) -> bool:
        """Create S3 bucket with proper configuration"""
        try:
            print(f"\n🪣 Creating S3 bucket: {self.bucket_name}")

            # Create bucket with location constraint for regions other than us-east-1
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            print(f"✅ Bucket created successfully: {self.bucket_name}")

            # Add tags to bucket
            self._add_bucket_tags()

            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"ℹ️  Bucket already exists and is owned by you: {self.bucket_name}")
                return True
            elif e.response['Error']['Code'] == 'BucketAlreadyExists':
                print(f"❌ Bucket name already taken globally. Trying with different name...")
                # Generate new name and retry
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                self.bucket_name = f"{self.project_prefix}-{self.account_id}-{random_suffix}"
                return self.create_bucket()
            else:
                print(f"❌ Failed to create bucket: {e}")
                return False

    def _add_bucket_tags(self) -> None:
        """Add tags to the bucket for cost tracking and organization"""
        tags = {
            'TagSet': [
                {'Key': 'project', 'Value': 'uci-research-poc'},
                {'Key': 'environment', 'Value': 'development'},
                {'Key': 'managed-by', 'Value': 's3_setup.py'},
                {'Key': 'cost-center', 'Value': 'research-department'},
                {'Key': 'data-classification', 'Value': 'research'},
                {'Key': 'created-date', 'Value': time.strftime('%Y-%m-%d')}
            ]
        }

        try:
            self.s3_client.put_bucket_tagging(
                Bucket=self.bucket_name,
                Tagging=tags
            )
            print("✅ Bucket tags applied")
        except ClientError as e:
            print(f"⚠️  Failed to add tags: {e}")

    def create_folder_structure(self) -> None:
        """Create folder structure in the bucket"""
        print("\n📁 Creating folder structure...")

        for folder in self.folders:
            try:
                # S3 doesn't have real folders, but we can create zero-byte objects with trailing slash
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder,
                    Body=b'',
                    ServerSideEncryption='AES256'
                )
                print(f"   ✅ Created: {folder}")
            except ClientError as e:
                print(f"   ❌ Failed to create {folder}: {e}")

        # Create README in each folder
        self._create_folder_readmes()

    def _create_folder_readmes(self) -> None:
        """Create README files in each folder explaining their purpose"""
        folder_descriptions = {
            'raw-data/': """# Raw Data Folder
This folder contains raw research documents, papers, and datasets.
- PDF research papers
- Text documents
- CSV/JSON datasets
- Web scraped content
""",
            'embeddings/': """# Embeddings Folder
This folder stores vector embeddings generated from research documents.
- Document embeddings (NPY/NPZ files)
- Metadata JSON files
- Embedding model artifacts
- Index files for vector search
""",
            'metadata/': """# Metadata Folder
This folder contains metadata about processed documents and system state.
- Document processing logs
- Index mappings
- Research paper metadata
- Author and citation information
""",
            'logs/': """# Logs Folder
This folder stores system and processing logs.
- Lambda execution logs
- Data processing logs
- Error logs
- Audit trails
"""
        }

        for folder, content in folder_descriptions.items():
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=f"{folder}README.md",
                    Body=content.encode('utf-8'),
                    ContentType='text/markdown',
                    ServerSideEncryption='AES256'
                )
            except ClientError:
                pass  # Silent fail for README creation

    def enable_versioning(self) -> None:
        """Enable versioning on the bucket"""
        print("\n📚 Enabling versioning...")

        try:
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            print("✅ Versioning enabled")
        except ClientError as e:
            print(f"❌ Failed to enable versioning: {e}")

    def setup_lifecycle_rules(self) -> None:
        """Set up lifecycle rules for cost optimization"""
        print("\n♻️  Setting up lifecycle rules for cost optimization...")

        lifecycle_configuration = {
            'Rules': [
                {
                    'ID': 'delete-old-versions',
                    'Status': 'Enabled',
                    'NoncurrentVersionExpiration': {
                        'NoncurrentDays': 7
                    },
                    'Filter': {'Prefix': ''}
                },
                {
                    'ID': 'transition-to-intelligent-tiering',
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': 0,
                            'StorageClass': 'INTELLIGENT_TIERING'
                        }
                    ],
                    'Filter': {'Prefix': ''}
                },
                {
                    'ID': 'delete-incomplete-multipart-uploads',
                    'Status': 'Enabled',
                    'AbortIncompleteMultipartUpload': {
                        'DaysAfterInitiation': 1
                    },
                    'Filter': {'Prefix': ''}
                },
                {
                    'ID': 'expire-old-logs',
                    'Status': 'Enabled',
                    'Expiration': {
                        'Days': 30
                    },
                    'Filter': {'Prefix': 'logs/'}
                },
                {
                    'ID': 'archive-old-raw-data',
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER_IR'
                        }
                    ],
                    'Filter': {'Prefix': 'raw-data/'}
                }
            ]
        }

        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_configuration
            )
            print("✅ Lifecycle rules configured:")
            print("   • Old versions deleted after 7 days")
            print("   • Intelligent-Tiering enabled for all objects")
            print("   • Logs expire after 30 days")
            print("   • Raw data archived to Glacier after 90 days")
            print("   • Incomplete uploads cleaned up after 1 day")
        except ClientError as e:
            print(f"❌ Failed to set lifecycle rules: {e}")

    def enable_encryption(self) -> None:
        """Enable default encryption for the bucket"""
        print("\n🔒 Enabling encryption at rest...")

        encryption_configuration = {
            'Rules': [
                {
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    },
                    'BucketKeyEnabled': True  # Reduces encryption costs
                }
            ]
        }

        try:
            self.s3_client.put_bucket_encryption(
                Bucket=self.bucket_name,
                ServerSideEncryptionConfiguration=encryption_configuration
            )
            print("✅ AES-256 encryption enabled")
            print("   • Bucket key enabled for cost reduction")
        except ClientError as e:
            print(f"❌ Failed to enable encryption: {e}")

    def setup_bucket_policy(self, lambda_role_arn: Optional[str] = None) -> None:
        """Set up bucket policy for Lambda access"""
        print("\n📋 Setting up bucket policy...")

        # If no Lambda role ARN provided, use a pattern that matches the expected role
        if not lambda_role_arn:
            lambda_role_arn = f"arn:aws:iam::{self.account_id}:role/uci-research-lambda-execution-role"

        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowLambdaAccess",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": lambda_role_arn
                    },
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.bucket_name}/*",
                        f"arn:aws:s3:::{self.bucket_name}"
                    ]
                },
                {
                    "Sid": "DenyUnencryptedObjectUploads",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*",
                    "Condition": {
                        "StringNotEquals": {
                            "s3:x-amz-server-side-encryption": "AES256"
                        }
                    }
                },
                {
                    "Sid": "DenyInsecureTransport",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:*",
                    "Resource": [
                        f"arn:aws:s3:::{self.bucket_name}/*",
                        f"arn:aws:s3:::{self.bucket_name}"
                    ],
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                }
            ]
        }

        try:
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print(f"✅ Bucket policy configured")
            print(f"   • Lambda role access: {lambda_role_arn}")
            print("   • Unencrypted uploads denied")
            print("   • Insecure transport denied")
        except ClientError as e:
            print(f"⚠️  Failed to set bucket policy: {e}")
            print("   You may need to update the Lambda role ARN after running iam_setup.py")

    def enable_intelligent_tiering(self) -> None:
        """Configure Intelligent-Tiering for additional cost optimization"""
        print("\n💰 Configuring Intelligent-Tiering...")

        intelligent_tiering_config = {
            'Id': 'uci-research-archive-config',
            'Status': 'Enabled',
            'Tierings': [
                {
                    'Days': 90,
                    'AccessTier': 'ARCHIVE_ACCESS'
                },
                {
                    'Days': 180,
                    'AccessTier': 'DEEP_ARCHIVE_ACCESS'
                }
            ],
            'Filter': {
                'Prefix': 'raw-data/'
            }
        }

        try:
            self.s3_client.put_bucket_intelligent_tiering_configuration(
                Bucket=self.bucket_name,
                Id='uci-research-archive-config',
                IntelligentTieringConfiguration=intelligent_tiering_config
            )
            print("✅ Intelligent-Tiering archive configuration set:")
            print("   • Archive tier after 90 days of no access")
            print("   • Deep Archive tier after 180 days of no access")
        except ClientError as e:
            print(f"⚠️  Failed to configure Intelligent-Tiering: {e}")

    def enable_cost_monitoring(self) -> None:
        """Enable S3 Storage Lens and cost allocation tags"""
        print("\n📊 Setting up cost monitoring...")

        # Enable request metrics
        try:
            self.s3_client.put_bucket_request_payment(
                Bucket=self.bucket_name,
                RequestPaymentConfiguration={
                    'Payer': 'BucketOwner'
                }
            )
            print("✅ Request payment configured (BucketOwner pays)")
        except ClientError:
            pass

        # Note about Storage Lens
        print("ℹ️  S3 Storage Lens provides free metrics at the organization level")
        print("   Access via AWS Console > S3 > Storage Lens")

    def save_configuration(self) -> None:
        """Save bucket configuration to a file"""
        config = {
            'bucket_name': self.bucket_name,
            'region': self.region,
            'account_id': self.account_id,
            'folders': self.folders,
            'created_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'bucket_arn': f"arn:aws:s3:::{self.bucket_name}",
            'console_url': f"https://s3.console.aws.amazon.com/s3/buckets/{self.bucket_name}"
        }

        filename = 's3_bucket_config.json'
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n📄 Configuration saved to: {filename}")

    def print_summary(self) -> None:
        """Print summary of the created bucket"""
        print("\n" + "="*60)
        print("S3 BUCKET SETUP COMPLETE")
        print("="*60)

        print(f"\n📌 Bucket Details:")
        print(f"   Name: {self.bucket_name}")
        print(f"   Region: {self.region}")
        print(f"   ARN: arn:aws:s3:::{self.bucket_name}")
        print(f"   Console URL: https://s3.console.aws.amazon.com/s3/buckets/{self.bucket_name}")

        print(f"\n📁 Folder Structure:")
        for folder in self.folders:
            print(f"   • {folder}")

        print(f"\n✨ Features Enabled:")
        print("   • Versioning with 7-day retention")
        print("   • AES-256 encryption at rest")
        print("   • Intelligent-Tiering for cost optimization")
        print("   • Lifecycle rules for automatic archival")
        print("   • Secure transport enforcement")
        print("   • Cost allocation tags")

        print(f"\n💡 Cost Optimization Measures:")
        print("   • Old versions deleted after 7 days")
        print("   • Logs expire after 30 days")
        print("   • Intelligent-Tiering moves infrequent data to cheaper storage")
        print("   • Raw data archived to Glacier after 90 days")
        print("   • Bucket key enabled for encryption cost reduction")

        print(f"\n🔧 Next Steps:")
        print("   1. Update Lambda functions to use this bucket")
        print("   2. Configure your application with the bucket name")
        print("   3. Upload research data to raw-data/ folder")
        print("   4. Monitor costs via AWS Cost Explorer")

    def test_bucket_access(self) -> bool:
        """Test basic bucket operations"""
        print("\n🧪 Testing bucket access...")

        test_key = 'test/test-file.txt'
        test_content = 'UCI Research Intelligence - S3 Test File'

        try:
            # Test write
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=test_content.encode('utf-8'),
                ServerSideEncryption='AES256'
            )
            print("   ✅ Write test successful")

            # Test read
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            content = response['Body'].read().decode('utf-8')
            assert content == test_content
            print("   ✅ Read test successful")

            # Test delete
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            print("   ✅ Delete test successful")

            return True

        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False

    def delete_bucket(self) -> None:
        """Delete the bucket and all its contents (use with caution!)"""
        print(f"\n⚠️  WARNING: This will delete bucket {self.bucket_name} and ALL its contents!")
        confirm = input("Type 'DELETE' to confirm: ")

        if confirm != 'DELETE':
            print("Deletion cancelled.")
            return

        try:
            # First, delete all objects in the bucket
            bucket = self.s3_resource.Bucket(self.bucket_name)
            bucket.objects.all().delete()
            bucket.object_versions.all().delete()

            # Then delete the bucket
            self.s3_client.delete_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket {self.bucket_name} deleted successfully")
        except ClientError as e:
            print(f"❌ Failed to delete bucket: {e}")

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("UCI RESEARCH INTELLIGENCE - S3 BUCKET SETUP")
    print("="*60)

    # Check for existing Lambda role ARN
    lambda_role_arn = None
    try:
        with open('iam_resources.json', 'r') as f:
            iam_config = json.load(f)
            roles = iam_config.get('created_resources', {}).get('roles', [])
            for role in roles:
                if 'lambda-execution-role' in role:
                    lambda_role_arn = role
                    print(f"\n✅ Found Lambda role from iam_setup.py: {lambda_role_arn}")
                    break
    except FileNotFoundError:
        print("\n⚠️  No IAM configuration found. Run iam_setup.py first for Lambda access.")

    # Initialize S3 setup
    s3_setup = S3Setup()

    # Create bucket
    if not s3_setup.create_bucket():
        print("❌ Failed to create bucket. Exiting.")
        sys.exit(1)

    # Set up bucket features
    s3_setup.create_folder_structure()
    s3_setup.enable_versioning()
    s3_setup.setup_lifecycle_rules()
    s3_setup.enable_encryption()
    s3_setup.setup_bucket_policy(lambda_role_arn)
    s3_setup.enable_intelligent_tiering()
    s3_setup.enable_cost_monitoring()

    # Test bucket access
    s3_setup.test_bucket_access()

    # Save configuration
    s3_setup.save_configuration()

    # Print summary
    s3_setup.print_summary()

    print("\n✅ S3 setup completed successfully!")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup S3 bucket for UCI Research Intelligence")
    parser.add_argument('--delete', action='store_true', help='Delete the created bucket')
    parser.add_argument('--test-only', action='store_true', help='Only test existing bucket access')

    args = parser.parse_args()

    if args.delete:
        # Load configuration and delete
        try:
            with open('s3_bucket_config.json', 'r') as f:
                config = json.load(f)
                s3_setup = S3Setup()
                s3_setup.bucket_name = config['bucket_name']
                s3_setup.delete_bucket()
        except FileNotFoundError:
            print("No bucket configuration found.")
    elif args.test_only:
        # Test existing bucket
        try:
            with open('s3_bucket_config.json', 'r') as f:
                config = json.load(f)
                s3_setup = S3Setup()
                s3_setup.bucket_name = config['bucket_name']
                s3_setup.test_bucket_access()
        except FileNotFoundError:
            print("No bucket configuration found. Run setup first.")
    else:
        main()