#!/usr/bin/env python3
"""
Upload collected research data to S3 with proper structure and verification.
Handles chunking for large files and creates comprehensive metadata index.
"""

import json
import os
import sys
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import defaultdict, Counter
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import math

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks for multipart upload
MIN_MULTIPART_SIZE = 10 * 1024 * 1024  # 10MB minimum for multipart

# S3 paths
S3_PATHS = {
    'papers': 'raw-data/papers/arxiv_papers.json',
    'faculty': 'raw-data/faculty/faculty_profiles.json',
    'grants': 'raw-data/grants/nsf_grants.json',
    'metadata': 'raw-data/metadata/collection_info.json'
}

class S3DataUploader:
    def __init__(self):
        """Initialize S3 uploader with bucket and client."""
        self.bucket_name = S3_BUCKET_NAME
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.data_dir = Path("data_generation")
        self.statistics = defaultdict(dict)

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def upload_file_with_progress(self, file_path: Path, s3_key: str) -> Dict[str, Any]:
        """Upload file to S3 with progress tracking and chunking support."""
        file_size = file_path.stat().st_size
        checksum = self.calculate_checksum(file_path)

        print(f"\n📤 Uploading: {file_path.name}")
        print(f"   Size: {self.format_bytes(file_size)}")
        print(f"   Destination: s3://{self.bucket_name}/{s3_key}")
        print(f"   Checksum: {checksum[:16]}...")

        start_time = time.time()

        try:
            if file_size > MIN_MULTIPART_SIZE:
                # Use multipart upload for large files
                self._multipart_upload(file_path, s3_key, file_size)
            else:
                # Regular upload for smaller files
                with open(file_path, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=f,
                        ServerSideEncryption='AES256',
                        Metadata={
                            'checksum': checksum,
                            'upload_timestamp': datetime.now().isoformat()
                        }
                    )

            upload_time = time.time() - start_time
            speed = file_size / upload_time if upload_time > 0 else 0

            print(f"   ✅ Upload complete in {upload_time:.1f}s ({self.format_bytes(speed)}/s)")

            # Verify upload
            verification = self._verify_upload(s3_key, checksum, file_size)

            return {
                'status': 'success',
                'file': file_path.name,
                's3_key': s3_key,
                'size': file_size,
                'checksum': checksum,
                'upload_time': upload_time,
                'verified': verification
            }

        except Exception as e:
            print(f"   ❌ Upload failed: {str(e)}")
            return {
                'status': 'failed',
                'file': file_path.name,
                'error': str(e)
            }

    def _multipart_upload(self, file_path: Path, s3_key: str, file_size: int):
        """Handle multipart upload for large files."""
        parts = []
        part_num = 0
        uploaded_bytes = 0

        # Initiate multipart upload with encryption
        response = self.s3_client.create_multipart_upload(
            Bucket=self.bucket_name,
            Key=s3_key,
            ServerSideEncryption='AES256'
        )
        upload_id = response['UploadId']

        try:
            with open(file_path, 'rb') as f:
                while uploaded_bytes < file_size:
                    part_num += 1
                    chunk = f.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    # Upload part
                    part_response = self.s3_client.upload_part(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        PartNumber=part_num,
                        UploadId=upload_id,
                        Body=chunk
                    )

                    parts.append({
                        'ETag': part_response['ETag'],
                        'PartNumber': part_num
                    })

                    uploaded_bytes += len(chunk)
                    progress = (uploaded_bytes / file_size) * 100
                    print(f"   Progress: {progress:.1f}% ({self.format_bytes(uploaded_bytes)}/{self.format_bytes(file_size)})", end='\r')

            print()  # New line after progress

            # Complete multipart upload
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )

        except Exception as e:
            # Abort upload on failure
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                UploadId=upload_id
            )
            raise e

    def _verify_upload(self, s3_key: str, expected_checksum: str, expected_size: int) -> Dict[str, Any]:
        """Verify uploaded file integrity."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            actual_size = response['ContentLength']
            stored_checksum = response.get('Metadata', {}).get('checksum', '')

            size_match = actual_size == expected_size
            checksum_match = stored_checksum == expected_checksum

            if size_match and checksum_match:
                print(f"   ✅ Verification passed")
            else:
                if not size_match:
                    print(f"   ⚠️ Size mismatch: expected {expected_size}, got {actual_size}")
                if not checksum_match:
                    print(f"   ⚠️ Checksum mismatch")

            return {
                'verified': size_match and checksum_match,
                'size_match': size_match,
                'checksum_match': checksum_match,
                'actual_size': actual_size
            }

        except Exception as e:
            print(f"   ⚠️ Verification failed: {str(e)}")
            return {
                'verified': False,
                'error': str(e)
            }

    def analyze_data(self, file_path: Path, data_type: str) -> Dict[str, Any]:
        """Analyze data file for statistics and metadata."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            if data_type == 'papers':
                return self._analyze_papers(data)
            elif data_type == 'faculty':
                return self._analyze_faculty(data)
            elif data_type == 'grants':
                return self._analyze_grants(data)
            else:
                return {'count': len(data) if isinstance(data, list) else 1}

        except Exception as e:
            return {'error': str(e)}

    def _analyze_papers(self, papers: List[Dict]) -> Dict[str, Any]:
        """Analyze paper data for statistics."""
        categories = Counter()
        years = Counter()
        research_areas = Counter()

        for paper in papers:
            # Count categories
            for cat in paper.get('categories', []):
                categories[cat] += 1

            # Extract year
            published = paper.get('published', '')
            if published:
                year = published[:4]
                years[year] += 1

            # Extract research areas from summary
            summary = paper.get('summary', '').lower()
            if 'quantum' in summary:
                research_areas['Quantum Physics'] += 1
            if 'machine learning' in summary or 'neural' in summary:
                research_areas['Machine Learning'] += 1
            if 'particle' in summary or 'collider' in summary:
                research_areas['Particle Physics'] += 1
            if 'astro' in summary or 'cosmic' in summary:
                research_areas['Astrophysics'] += 1
            if 'condens' in summary or 'material' in summary:
                research_areas['Condensed Matter'] += 1

        return {
            'total_papers': len(papers),
            'categories': dict(categories.most_common(10)),
            'year_distribution': dict(sorted(years.items())),
            'top_research_areas': dict(research_areas.most_common(5)),
            'avg_authors_per_paper': sum(len(p.get('authors', [])) for p in papers) / len(papers) if papers else 0
        }

    def _analyze_faculty(self, faculty: List[Dict]) -> Dict[str, Any]:
        """Analyze faculty data for statistics."""
        departments = Counter()
        research_interests = Counter()

        for member in faculty:
            dept = member.get('department', 'Unknown')
            departments[dept] += 1

            for interest in member.get('research_interests', []):
                research_interests[interest] += 1

        return {
            'total_faculty': len(faculty),
            'departments': dict(departments),
            'top_research_interests': dict(research_interests.most_common(10)),
            'avg_interests_per_faculty': sum(len(f.get('research_interests', [])) for f in faculty) / len(faculty) if faculty else 0
        }

    def _analyze_grants(self, grants: List[Dict]) -> Dict[str, Any]:
        """Analyze grant data for statistics."""
        years = Counter()
        total_amount = 0

        for grant in grants:
            year = grant.get('year', 'Unknown')
            years[year] += 1

            amount = grant.get('amount', 0)
            if isinstance(amount, (int, float)):
                total_amount += amount

        return {
            'total_grants': len(grants),
            'year_distribution': dict(sorted(years.items())),
            'total_funding': total_amount,
            'avg_grant_amount': total_amount / len(grants) if grants else 0
        }

    def create_metadata_index(self, upload_results: List[Dict]) -> Dict[str, Any]:
        """Create comprehensive metadata index."""
        metadata = {
            'collection_timestamp': datetime.now().isoformat(),
            'upload_timestamp': datetime.now().isoformat(),
            'bucket_name': self.bucket_name,
            'region': AWS_REGION,
            'files_uploaded': [],
            'statistics': self.statistics,
            'upload_summary': {
                'total_files': len(upload_results),
                'successful': sum(1 for r in upload_results if r.get('status') == 'success'),
                'failed': sum(1 for r in upload_results if r.get('status') == 'failed'),
                'total_size': sum(r.get('size', 0) for r in upload_results if r.get('status') == 'success'),
                'total_upload_time': sum(r.get('upload_time', 0) for r in upload_results if r.get('status') == 'success')
            }
        }

        for result in upload_results:
            if result.get('status') == 'success':
                metadata['files_uploaded'].append({
                    'file_name': result['file'],
                    's3_key': result['s3_key'],
                    'size': result['size'],
                    'checksum': result['checksum'],
                    'verified': result.get('verified', {}).get('verified', False)
                })

        return metadata

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"

    def run(self):
        """Main execution method."""
        print("\n" + "="*60)
        print("🚀 UCI Research Data S3 Upload Tool")
        print("="*60)

        if not self.bucket_name:
            print("❌ Error: S3_BUCKET_NAME not found in .env file")
            return

        print(f"\n📦 Target Bucket: {self.bucket_name}")
        print(f"🌎 Region: {AWS_REGION}")

        # Check for combined data file
        combined_file = self.data_dir / "uci_research_data.json"

        if not combined_file.exists():
            print("\n❌ No data files found. Please run collect_arxiv_data.py first.")
            return

        print(f"✅ Found: {combined_file.name}")

        # Load the combined data
        with open(combined_file, 'r') as f:
            all_data = json.load(f)

        # Upload files
        upload_results = []

        # Split and upload individual data types
        data_types_to_upload = {
            'papers': all_data.get('papers', []),
            'faculty': all_data.get('faculty', []),
            'grants': all_data.get('grants', [])
        }

        for data_type, data in data_types_to_upload.items():
            if data:
                # Create temporary file for this data type
                temp_file = self.data_dir / f"{data_type}_temp.json"
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2)

                # Analyze data
                print(f"\n📊 Analyzing {data_type} data...")
                stats = self.analyze_data(temp_file, data_type)
                self.statistics[data_type] = stats

                # Upload to S3
                s3_key = S3_PATHS.get(data_type, f"raw-data/{data_type}/{data_type}.json")
                result = self.upload_file_with_progress(temp_file, s3_key)
                upload_results.append(result)

                # Clean up temp file
                temp_file.unlink()

        # Create and upload metadata index
        print("\n📝 Creating metadata index...")
        metadata = self.create_metadata_index(upload_results)

        # Save metadata locally
        metadata_file = self.data_dir / "upload_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Upload metadata to S3
        metadata_result = self.upload_file_with_progress(
            metadata_file,
            S3_PATHS['metadata']
        )
        upload_results.append(metadata_result)

        # Print summary
        print("\n" + "="*60)
        print("📋 Upload Summary")
        print("="*60)

        successful = sum(1 for r in upload_results if r.get('status') == 'success')
        failed = sum(1 for r in upload_results if r.get('status') == 'failed')
        total_size = sum(r.get('size', 0) for r in upload_results if r.get('status') == 'success')

        print(f"✅ Successful uploads: {successful}")
        print(f"❌ Failed uploads: {failed}")
        print(f"💾 Total data uploaded: {self.format_bytes(total_size)}")

        # Print statistics
        print("\n📊 Data Statistics:")
        for data_type, stats in self.statistics.items():
            print(f"\n{data_type.upper()}:")
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in list(value.items())[:5]:
                        print(f"    - {k}: {v}")
                elif isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")

        # Print S3 paths
        print("\n📂 S3 File Locations:")
        for result in upload_results:
            if result.get('status') == 'success':
                print(f"  s3://{self.bucket_name}/{result['s3_key']}")

        print("\n✨ Upload complete! Data is now available in S3.")
        print(f"🔍 View in AWS Console: https://s3.console.aws.amazon.com/s3/buckets/{self.bucket_name}")

if __name__ == "__main__":
    uploader = S3DataUploader()
    uploader.run()