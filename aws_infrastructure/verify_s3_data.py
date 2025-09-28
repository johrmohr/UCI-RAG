#!/usr/bin/env python3
"""
Verify S3 data upload and provide comprehensive bucket analysis.
Checks data integrity, calculates storage, and samples content.
"""

import json
import os
import sys
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')

class S3DataVerifier:
    def __init__(self):
        """Initialize S3 verifier."""
        self.bucket_name = S3_BUCKET_NAME
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.bucket_contents = defaultdict(list)
        self.total_size = 0
        self.file_count = 0
        self.verification_results = {}

    def list_bucket_contents(self) -> bool:
        """List all files in the S3 bucket."""
        print(f"\n📂 Listing contents of bucket: {self.bucket_name}")
        print("-" * 50)

        try:
            # Use paginator for large buckets
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)

            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        size = obj['Size']
                        modified = obj['LastModified']

                        # Categorize by folder
                        folder = key.split('/')[0] if '/' in key else 'root'
                        self.bucket_contents[folder].append({
                            'key': key,
                            'size': size,
                            'modified': modified,
                            'size_human': self.format_bytes(size)
                        })

                        self.total_size += size
                        self.file_count += 1

            if self.file_count == 0:
                print("⚠️ Bucket is empty!")
                return False

            # Print organized contents
            for folder, files in sorted(self.bucket_contents.items()):
                print(f"\n📁 {folder}/")
                for file_info in files:
                    # Show relative path within folder
                    relative_path = file_info['key'].replace(f"{folder}/", "") if folder != 'root' else file_info['key']
                    print(f"   📄 {relative_path} ({file_info['size_human']})")
                    print(f"      Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")

            return True

        except ClientError as e:
            print(f"❌ Error listing bucket: {e}")
            return False

    def verify_metadata(self) -> Dict[str, Any]:
        """Download and verify the metadata/collection_info.json file."""
        print(f"\n🔍 Verifying metadata file...")
        print("-" * 50)

        metadata_key = 'raw-data/metadata/collection_info.json'

        try:
            # Download metadata to temp file
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as tmp:
                self.s3_client.download_file(self.bucket_name, metadata_key, tmp.name)
                tmp_path = tmp.name

            # Read and parse metadata
            with open(tmp_path, 'r') as f:
                metadata = json.load(f)

            # Clean up temp file
            os.unlink(tmp_path)

            print("✅ Metadata file downloaded successfully")

            # Display metadata summary
            if 'collection_timestamp' in metadata:
                print(f"   📅 Collection time: {metadata['collection_timestamp']}")
            if 'upload_timestamp' in metadata:
                print(f"   📤 Upload time: {metadata['upload_timestamp']}")

            if 'files_uploaded' in metadata:
                print(f"\n   📊 Files in metadata:")
                for file_info in metadata['files_uploaded']:
                    print(f"      • {file_info['file_name']} ({self.format_bytes(file_info['size'])})")
                    if 'verified' in file_info:
                        status = "✅" if file_info['verified'] else "⚠️"
                        print(f"        Verification: {status}")

            if 'statistics' in metadata:
                print(f"\n   📈 Data Statistics:")
                stats = metadata['statistics']

                for data_type, type_stats in stats.items():
                    if isinstance(type_stats, dict):
                        print(f"\n      {data_type.upper()}:")
                        for key, value in type_stats.items():
                            if not isinstance(value, dict):
                                if isinstance(value, float):
                                    print(f"        • {key}: {value:.2f}")
                                else:
                                    print(f"        • {key}: {value}")

            self.verification_results['metadata'] = metadata
            return metadata

        except ClientError as e:
            print(f"❌ Error downloading metadata: {e}")
            self.verification_results['metadata'] = None
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing metadata JSON: {e}")
            self.verification_results['metadata'] = None
            return None

    def verify_data_folders(self) -> Dict[str, bool]:
        """Check that papers, faculty, and grants folders have data."""
        print(f"\n📋 Verifying data folders...")
        print("-" * 50)

        expected_folders = {
            'papers': 'raw-data/papers/',
            'faculty': 'raw-data/faculty/',
            'grants': 'raw-data/grants/'
        }

        folder_status = {}

        for folder_name, prefix in expected_folders.items():
            try:
                # Check if folder has any objects
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=1
                )

                has_data = 'Contents' in response and len(response['Contents']) > 0

                if has_data:
                    # Get more details about the folder contents
                    full_response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=prefix
                    )

                    if 'Contents' in full_response:
                        total_size = sum(obj['Size'] for obj in full_response['Contents'])
                        file_count = len(full_response['Contents'])

                        print(f"✅ {folder_name}/ - {file_count} file(s), {self.format_bytes(total_size)}")
                        folder_status[folder_name] = {
                            'exists': True,
                            'file_count': file_count,
                            'total_size': total_size
                        }
                    else:
                        folder_status[folder_name] = {'exists': True, 'file_count': 0}
                else:
                    print(f"⚠️ {folder_name}/ - No data found")
                    folder_status[folder_name] = {'exists': False}

            except ClientError as e:
                print(f"❌ Error checking {folder_name}: {e}")
                folder_status[folder_name] = {'exists': False, 'error': str(e)}

        self.verification_results['folders'] = folder_status
        return folder_status

    def sample_paper_data(self) -> Optional[Dict[str, Any]]:
        """Download and sample one paper from S3 to verify readability."""
        print(f"\n🔬 Sampling paper data...")
        print("-" * 50)

        papers_key = 'raw-data/papers/arxiv_papers.json'

        try:
            # Download papers file to temp
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as tmp:
                print(f"   Downloading {papers_key}...")
                self.s3_client.download_file(self.bucket_name, papers_key, tmp.name)
                tmp_path = tmp.name

            # Read and parse papers
            with open(tmp_path, 'r') as f:
                papers = json.load(f)

            # Clean up temp file
            os.unlink(tmp_path)

            if not papers:
                print("⚠️ Papers file is empty")
                return None

            print(f"✅ Successfully loaded {len(papers)} papers")

            # Sample the first paper
            sample_paper = papers[0] if papers else None

            if sample_paper:
                print(f"\n   📄 Sample Paper:")
                print(f"      Title: {sample_paper.get('title', 'N/A')[:80]}...")
                print(f"      Authors: {', '.join(sample_paper.get('authors', [])[:3])}")
                if len(sample_paper.get('authors', [])) > 3:
                    print(f"               (+{len(sample_paper.get('authors', [])) - 3} more)")
                print(f"      Categories: {', '.join(sample_paper.get('categories', []))}")
                print(f"      Published: {sample_paper.get('published', 'N/A')[:10]}")

                summary = sample_paper.get('summary', '')
                if summary:
                    print(f"      Summary: {summary[:150]}...")

                self.verification_results['sample_paper'] = sample_paper
                return sample_paper

        except ClientError as e:
            print(f"❌ Error downloading papers: {e}")
            self.verification_results['sample_paper'] = None
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing papers JSON: {e}")
            self.verification_results['sample_paper'] = None
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.verification_results['sample_paper'] = None
            return None

    def calculate_storage_summary(self) -> Dict[str, Any]:
        """Calculate total storage used and provide cost estimates."""
        print(f"\n💾 Storage Summary")
        print("-" * 50)

        # S3 pricing (approximate, varies by region)
        storage_cost_per_gb_month = 0.023  # USD
        request_cost_per_1000_get = 0.0004  # USD
        request_cost_per_1000_put = 0.005  # USD

        gb_used = self.total_size / (1024 ** 3)
        estimated_monthly_cost = gb_used * storage_cost_per_gb_month

        summary = {
            'total_files': self.file_count,
            'total_size_bytes': self.total_size,
            'total_size_human': self.format_bytes(self.total_size),
            'size_gb': round(gb_used, 4),
            'estimated_monthly_storage_cost': round(estimated_monthly_cost, 4),
            'breakdown_by_folder': {}
        }

        print(f"📊 Total files: {self.file_count}")
        print(f"💿 Total size: {self.format_bytes(self.total_size)} ({gb_used:.4f} GB)")
        print(f"💰 Estimated monthly storage cost: ${estimated_monthly_cost:.4f}")

        # Breakdown by folder
        print(f"\n📁 Storage by folder:")
        for folder, files in self.bucket_contents.items():
            folder_size = sum(f['size'] for f in files)
            folder_percentage = (folder_size / self.total_size * 100) if self.total_size > 0 else 0
            summary['breakdown_by_folder'][folder] = {
                'files': len(files),
                'size': folder_size,
                'size_human': self.format_bytes(folder_size),
                'percentage': round(folder_percentage, 2)
            }
            print(f"   {folder}/: {len(files)} files, {self.format_bytes(folder_size)} ({folder_percentage:.1f}%)")

        self.verification_results['storage_summary'] = summary
        return summary

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"

    def print_final_summary(self):
        """Print a pretty summary of the bucket verification."""
        print("\n" + "="*60)
        print("✨ S3 BUCKET VERIFICATION COMPLETE")
        print("="*60)

        print(f"\n🪣 Bucket: {self.bucket_name}")
        print(f"🌎 Region: {AWS_REGION}")

        # Overall health check
        health_checks = []

        # Check metadata
        if self.verification_results.get('metadata'):
            health_checks.append(("Metadata file", "✅"))
        else:
            health_checks.append(("Metadata file", "❌"))

        # Check folders
        folders = self.verification_results.get('folders', {})
        for folder_name in ['papers', 'faculty', 'grants']:
            if folder_name in folders and folders[folder_name].get('exists'):
                health_checks.append((f"{folder_name.capitalize()} data", "✅"))
            else:
                health_checks.append((f"{folder_name.capitalize()} data", "⚠️"))

        # Check sample paper
        if self.verification_results.get('sample_paper'):
            health_checks.append(("Paper readability", "✅"))
        else:
            health_checks.append(("Paper readability", "❌"))

        print(f"\n🏥 Health Checks:")
        for check_name, status in health_checks:
            print(f"   {status} {check_name}")

        # Data availability
        print(f"\n📊 Data Availability:")
        if folders.get('papers', {}).get('file_count'):
            print(f"   • Papers: {folders['papers']['file_count']} file(s)")
        if folders.get('faculty', {}).get('file_count'):
            print(f"   • Faculty: {folders['faculty']['file_count']} file(s)")
        if folders.get('grants', {}).get('file_count'):
            print(f"   • Grants: {folders['grants']['file_count']} file(s)")

        # Storage summary
        storage = self.verification_results.get('storage_summary', {})
        if storage:
            print(f"\n💾 Storage Usage:")
            print(f"   • Total: {storage['total_size_human']}")
            print(f"   • Files: {storage['total_files']}")
            print(f"   • Monthly cost: ${storage['estimated_monthly_storage_cost']:.4f}")

        # Overall status
        all_good = all(status == "✅" for _, status in health_checks[:5])

        print(f"\n🎯 Overall Status: {'✅ Ready for next step' if all_good else '⚠️ Some issues found'}")

        if all_good:
            print("\n✨ Your S3 data is properly uploaded and verified!")
            print("   The bucket is ready for RAG system integration.")
        else:
            print("\n⚠️ Please review the issues above before proceeding.")

    def save_verification_report(self):
        """Save verification report to file."""
        report_file = Path("aws_infrastructure/s3_verification_report.json")

        report = {
            'timestamp': datetime.now().isoformat(),
            'bucket_name': self.bucket_name,
            'region': AWS_REGION,
            'verification_results': self.verification_results,
            'summary': {
                'total_files': self.file_count,
                'total_size': self.total_size,
                'folders_checked': list(self.verification_results.get('folders', {}).keys()),
                'metadata_valid': bool(self.verification_results.get('metadata')),
                'sample_readable': bool(self.verification_results.get('sample_paper'))
            }
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Verification report saved to: {report_file}")

    def run(self):
        """Main execution method."""
        print("\n" + "="*60)
        print("🔍 S3 Data Verification Tool")
        print("="*60)

        if not self.bucket_name:
            print("❌ Error: S3_BUCKET_NAME not found in .env file")
            return

        print(f"Starting verification of S3 bucket: {self.bucket_name}")

        # 1. List all files
        if not self.list_bucket_contents():
            print("❌ Failed to list bucket contents")
            return

        # 2. Verify metadata
        self.verify_metadata()

        # 3. Check data folders
        self.verify_data_folders()

        # 4. Calculate storage
        self.calculate_storage_summary()

        # 5. Sample paper data
        self.sample_paper_data()

        # 6. Print final summary
        self.print_final_summary()

        # 7. Save report
        self.save_verification_report()

if __name__ == "__main__":
    verifier = S3DataVerifier()
    verifier.run()