#!/usr/bin/env python3
"""
IAM Setup Script for UCI Research Intelligence POC
Creates minimal IAM roles and policies for the research intelligence system
"""

import json
import sys
import time
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class IAMSetup:
    """Manages IAM role and policy creation for the UCI Research Intelligence system"""

    def __init__(self, project_prefix: str = "uci-research"):
        """
        Initialize IAM setup with project prefix for resource naming

        Args:
            project_prefix: Prefix for all created resources
        """
        self.project_prefix = project_prefix
        self.region = boto3.Session().region_name or 'us-west-2'

        try:
            self.iam = boto3.client('iam')
            self.sts = boto3.client('sts')
            self.account_id = self.sts.get_caller_identity()['Account']
            print(f"✅ Connected to AWS Account: {self.account_id}")
            print(f"   Region: {self.region}")
        except NoCredentialsError:
            print("❌ No AWS credentials found. Please run 'aws configure' first.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to connect to AWS: {e}")
            sys.exit(1)

        self.created_resources = {
            'roles': [],
            'policies': [],
            'role_policies': []
        }

    def create_lambda_execution_role(self) -> Optional[str]:
        """Create IAM role for Lambda function execution"""
        role_name = f"{self.project_prefix}-lambda-execution-role"

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        try:
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Execution role for UCI Research Intelligence Lambda functions",
                Tags=[
                    {'Key': 'Project', 'Value': 'UCI-Research-Intelligence'},
                    {'Key': 'Environment', 'Value': 'POC'},
                    {'Key': 'ManagedBy', 'Value': 'iam_setup.py'}
                ]
            )
            role_arn = response['Role']['Arn']
            print(f"✅ Created Lambda execution role: {role_name}")
            self.created_resources['roles'].append(role_arn)
            return role_arn

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                role = self.iam.get_role(RoleName=role_name)
                role_arn = role['Role']['Arn']
                print(f"ℹ️  Lambda execution role already exists: {role_name}")
                return role_arn
            else:
                print(f"❌ Failed to create Lambda execution role: {e}")
                return None

    def create_s3_access_policy(self) -> Optional[str]:
        """Create policy for S3 bucket access"""
        policy_name = f"{self.project_prefix}-s3-access-policy"

        # Minimal S3 permissions for POC
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "S3BucketList",
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListBucket",
                        "s3:GetBucketLocation",
                        "s3:GetBucketVersioning"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.project_prefix}-*"
                    ]
                },
                {
                    "Sid": "S3ObjectAccess",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:GetObjectVersion"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.project_prefix}-*/*"
                    ]
                }
            ]
        }

        return self._create_policy(policy_name, policy_document, "S3 access for research data")

    def create_opensearch_access_policy(self) -> Optional[str]:
        """Create policy for OpenSearch access"""
        policy_name = f"{self.project_prefix}-opensearch-access-policy"

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "OpenSearchDomainAccess",
                    "Effect": "Allow",
                    "Action": [
                        "es:ESHttpGet",
                        "es:ESHttpPost",
                        "es:ESHttpPut",
                        "es:ESHttpDelete",
                        "es:ESHttpHead"
                    ],
                    "Resource": [
                        f"arn:aws:es:{self.region}:{self.account_id}:domain/{self.project_prefix}-*/*"
                    ]
                },
                {
                    "Sid": "OpenSearchClusterAccess",
                    "Effect": "Allow",
                    "Action": [
                        "es:DescribeElasticsearchDomain",
                        "es:DescribeElasticsearchDomains",
                        "es:DescribeElasticsearchDomainConfig",
                        "es:ListDomainNames"
                    ],
                    "Resource": "*"
                }
            ]
        }

        return self._create_policy(policy_name, policy_document, "OpenSearch access for vector search")

    def create_bedrock_access_policy(self) -> Optional[str]:
        """Create policy for AWS Bedrock (AI/ML) access"""
        policy_name = f"{self.project_prefix}-bedrock-access-policy"

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockModelAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{self.region}::foundation-model/*"
                    ]
                },
                {
                    "Sid": "BedrockListModels",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:ListFoundationModels",
                        "bedrock:GetFoundationModel"
                    ],
                    "Resource": "*"
                }
            ]
        }

        return self._create_policy(policy_name, policy_document, "Bedrock AI/ML model access")

    def create_cloudwatch_logs_policy(self) -> Optional[str]:
        """Create policy for CloudWatch Logs access"""
        policy_name = f"{self.project_prefix}-cloudwatch-logs-policy"

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "CloudWatchLogsAccess",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": [
                        f"arn:aws:logs:{self.region}:{self.account_id}:log-group:/aws/lambda/{self.project_prefix}-*",
                        f"arn:aws:logs:{self.region}:{self.account_id}:log-group:/aws/lambda/{self.project_prefix}-*:*"
                    ]
                }
            ]
        }

        return self._create_policy(policy_name, policy_document, "CloudWatch Logs for monitoring")

    def create_opensearch_service_role(self) -> Optional[str]:
        """Create service role for OpenSearch domain"""
        role_name = f"{self.project_prefix}-opensearch-service-role"

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "es.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        try:
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Service role for UCI Research Intelligence OpenSearch domain",
                Tags=[
                    {'Key': 'Project', 'Value': 'UCI-Research-Intelligence'},
                    {'Key': 'Environment', 'Value': 'POC'},
                    {'Key': 'ManagedBy', 'Value': 'iam_setup.py'}
                ]
            )
            role_arn = response['Role']['Arn']
            print(f"✅ Created OpenSearch service role: {role_name}")
            self.created_resources['roles'].append(role_arn)

            # Attach AWS managed policy for OpenSearch
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonOpenSearchServiceCognitoAccess'
            )

            return role_arn

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                role = self.iam.get_role(RoleName=role_name)
                role_arn = role['Role']['Arn']
                print(f"ℹ️  OpenSearch service role already exists: {role_name}")
                return role_arn
            else:
                print(f"❌ Failed to create OpenSearch service role: {e}")
                return None

    def _create_policy(self, policy_name: str, policy_document: Dict, description: str) -> Optional[str]:
        """Helper method to create an IAM policy"""
        try:
            response = self.iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description=description,
                Tags=[
                    {'Key': 'Project', 'Value': 'UCI-Research-Intelligence'},
                    {'Key': 'Environment', 'Value': 'POC'},
                    {'Key': 'ManagedBy', 'Value': 'iam_setup.py'}
                ]
            )
            policy_arn = response['Policy']['Arn']
            print(f"✅ Created policy: {policy_name}")
            self.created_resources['policies'].append(policy_arn)
            return policy_arn

        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                # Get existing policy ARN
                policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
                print(f"ℹ️  Policy already exists: {policy_name}")
                return policy_arn
            else:
                print(f"❌ Failed to create policy {policy_name}: {e}")
                return None

    def attach_policies_to_lambda_role(self, role_name: str, policy_arns: List[str]) -> bool:
        """Attach policies to the Lambda execution role"""
        success = True
        for policy_arn in policy_arns:
            if policy_arn:
                try:
                    self.iam.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                    print(f"  ✅ Attached policy to Lambda role: {policy_arn.split('/')[-1]}")
                    self.created_resources['role_policies'].append((role_name, policy_arn))
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AttachedPolicyNotFound':
                        print(f"  ⚠️  Policy not found: {policy_arn}")
                    else:
                        print(f"  ❌ Failed to attach policy: {e}")
                    success = False

        # Attach AWS managed Lambda execution policy
        try:
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            print(f"  ✅ Attached AWS managed Lambda execution policy")
        except ClientError:
            pass  # Already attached

        return success

    def save_configuration(self, filename: str = "iam_resources.json") -> None:
        """Save created IAM resources to a JSON file for reference"""
        config = {
            "account_id": self.account_id,
            "region": self.region,
            "project_prefix": self.project_prefix,
            "created_resources": self.created_resources,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n📄 Configuration saved to: {filename}")

    def print_summary(self) -> None:
        """Print summary of created resources"""
        print("\n" + "="*60)
        print("IAM SETUP SUMMARY")
        print("="*60)
        print(f"\nAccount ID: {self.account_id}")
        print(f"Region: {self.region}")
        print(f"Project Prefix: {self.project_prefix}")

        if self.created_resources['roles']:
            print("\n📋 Created Roles:")
            for arn in self.created_resources['roles']:
                print(f"   • {arn}")

        if self.created_resources['policies']:
            print("\n📜 Created Policies:")
            for arn in self.created_resources['policies']:
                print(f"   • {arn}")

        print("\n🔧 Next Steps:")
        print("1. Update Lambda functions to use the execution role")
        print("2. Configure OpenSearch domain with the service role")
        print("3. Update S3 bucket names to match the prefix pattern")
        print("4. Test permissions with verify_iam_setup.py")

    def cleanup(self) -> None:
        """Remove all created IAM resources (use with caution!)"""
        print("\n⚠️  WARNING: This will delete all IAM resources created by this script!")
        confirm = input("Type 'DELETE' to confirm: ")

        if confirm != 'DELETE':
            print("Cleanup cancelled.")
            return

        # Detach policies from roles first
        for role_name, policy_arn in self.created_resources['role_policies']:
            try:
                self.iam.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                print(f"✅ Detached policy from role: {role_name}")
            except Exception as e:
                print(f"❌ Failed to detach policy: {e}")

        # Delete policies
        for policy_arn in self.created_resources['policies']:
            try:
                self.iam.delete_policy(PolicyArn=policy_arn)
                print(f"✅ Deleted policy: {policy_arn}")
            except Exception as e:
                print(f"❌ Failed to delete policy: {e}")

        # Delete roles
        for role_arn in self.created_resources['roles']:
            role_name = role_arn.split('/')[-1]
            try:
                self.iam.delete_role(RoleName=role_name)
                print(f"✅ Deleted role: {role_name}")
            except Exception as e:
                print(f"❌ Failed to delete role: {e}")

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("UCI RESEARCH INTELLIGENCE - IAM SETUP")
    print("="*60 + "\n")

    # Initialize IAM setup
    iam_setup = IAMSetup(project_prefix="uci-research")

    # Create Lambda execution role
    print("\n🔨 Creating Lambda Execution Role...")
    lambda_role_arn = iam_setup.create_lambda_execution_role()
    lambda_role_name = lambda_role_arn.split('/')[-1] if lambda_role_arn else None

    # Create policies
    print("\n📜 Creating IAM Policies...")
    s3_policy_arn = iam_setup.create_s3_access_policy()
    opensearch_policy_arn = iam_setup.create_opensearch_access_policy()
    bedrock_policy_arn = iam_setup.create_bedrock_access_policy()
    cloudwatch_policy_arn = iam_setup.create_cloudwatch_logs_policy()

    # Create OpenSearch service role
    print("\n🔨 Creating OpenSearch Service Role...")
    opensearch_role_arn = iam_setup.create_opensearch_service_role()

    # Attach policies to Lambda role
    if lambda_role_name:
        print(f"\n🔗 Attaching Policies to Lambda Role...")
        policies = [
            s3_policy_arn,
            opensearch_policy_arn,
            bedrock_policy_arn,
            cloudwatch_policy_arn
        ]
        iam_setup.attach_policies_to_lambda_role(lambda_role_name, policies)

    # Save configuration
    iam_setup.save_configuration()

    # Print summary
    iam_setup.print_summary()

    print("\n✅ IAM setup completed successfully!")
    print("\n💡 Tip: Run this script again to verify all resources exist (idempotent)")

    # Optional cleanup prompt
    print("\n⚠️  To clean up resources, run: python iam_setup.py --cleanup")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup IAM roles and policies for UCI Research Intelligence")
    parser.add_argument('--cleanup', action='store_true', help='Remove all created IAM resources')
    parser.add_argument('--prefix', default='uci-research', help='Project prefix for resource naming')

    args = parser.parse_args()

    if args.cleanup:
        iam_setup = IAMSetup(project_prefix=args.prefix)
        # Load previous configuration if exists
        try:
            with open('iam_resources.json', 'r') as f:
                config = json.load(f)
                iam_setup.created_resources = config.get('created_resources', {})
        except FileNotFoundError:
            print("No previous configuration found. Nothing to clean up.")
            sys.exit(0)

        iam_setup.cleanup()
    else:
        main()