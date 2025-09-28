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
