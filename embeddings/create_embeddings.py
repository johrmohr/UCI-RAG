#!/usr/bin/env python3
"""
Create embeddings for research papers using sentence-transformers.
Downloads data from S3 and generates weighted embeddings for different fields.
Optimized for CPU usage on Mac.
"""

import json
import os
import sys
import pickle
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import numpy as np
import boto3
from botocore.exceptions import ClientError
import psutil
from tqdm import tqdm
import gc
from collections import defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

# Import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("❌ sentence-transformers not installed. Please run:")
    print("   pip install sentence-transformers")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')

# Model configuration - using lightweight model for efficiency
MODEL_NAME = 'all-MiniLM-L6-v2'  # 384-dimensional embeddings, fast and efficient
MAX_TOKEN_LENGTH = 512
BATCH_SIZE = 32  # Adjust based on available memory

# Weights for different fields
FIELD_WEIGHTS = {
    'title': 1.5,
    'abstract': 1.0,
    'authors': 0.5,
    'categories': 0.3,
    'keywords': 0.8
}

class EmbeddingsGenerator:
    def __init__(self, use_cache=True):
        """Initialize the embeddings generator."""
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.bucket_name = S3_BUCKET_NAME
        self.model = None
        self.use_cache = use_cache
        self.cache_dir = Path("embeddings/cache")
        self.output_dir = Path("embeddings/output")

        # Create directories
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Track statistics
        self.stats = {
            'papers_processed': 0,
            'faculty_processed': 0,
            'chunks_created': 0,
            'total_embeddings': 0,
            'memory_usage': {}
        }

    def load_model(self):
        """Load the sentence transformer model."""
        print(f"\n🤖 Loading model: {MODEL_NAME}")
        print("   This may take a minute on first run...")

        # Force CPU usage for Mac compatibility
        import torch
        torch.set_num_threads(4)  # Optimize for CPU

        self.model = SentenceTransformer(MODEL_NAME, device='cpu')

        print(f"✅ Model loaded successfully")
        print(f"   Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        print(f"   Max sequence length: {self.model.max_seq_length}")

    def download_from_s3(self, s3_key: str, local_path: Path) -> bool:
        """Download file from S3 with caching."""
        if self.use_cache and local_path.exists():
            print(f"   Using cached file: {local_path.name}")
            return True

        try:
            print(f"   Downloading: {s3_key}")
            self.s3_client.download_file(self.bucket_name, s3_key, str(local_path))
            print(f"   ✅ Downloaded to {local_path.name}")
            return True
        except ClientError as e:
            print(f"   ❌ Error downloading {s3_key}: {e}")
            return False

    def chunk_text(self, text: str, max_length: int = MAX_TOKEN_LENGTH) -> List[str]:
        """Chunk long text into smaller segments."""
        # Simple word-based chunking
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > max_length * 3:  # Rough estimate (3 chars per token)
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks if chunks else [text[:max_length * 3]]

    def create_weighted_embedding(self, fields: Dict[str, str]) -> np.ndarray:
        """Create a weighted embedding from multiple fields."""
        embeddings = []
        weights = []

        for field_name, text in fields.items():
            if text and field_name in FIELD_WEIGHTS:
                # Generate embedding for this field
                embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
                embeddings.append(embedding)
                weights.append(FIELD_WEIGHTS[field_name])

        if not embeddings:
            # Return zero embedding if no fields
            return np.zeros(self.model.get_sentence_embedding_dimension())

        # Weighted average of embeddings
        embeddings = np.array(embeddings)
        weights = np.array(weights)
        weights = weights / weights.sum()  # Normalize weights

        weighted_embedding = np.average(embeddings, axis=0, weights=weights)

        # Normalize the final embedding
        norm = np.linalg.norm(weighted_embedding)
        if norm > 0:
            weighted_embedding = weighted_embedding / norm

        return weighted_embedding

    def process_papers(self, papers: List[Dict]) -> Dict[str, Any]:
        """Process papers and create embeddings."""
        print(f"\n📚 Processing {len(papers)} papers...")

        paper_embeddings = []
        paper_metadata = []

        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with tqdm(total=len(papers), desc="Creating embeddings") as pbar:
            for paper in papers:
                # Extract fields
                title = paper.get('title', '')
                abstract = paper.get('summary', '')
                authors = ', '.join(paper.get('authors', []))
                categories = ', '.join(paper.get('categories', []))

                # Handle long abstracts with chunking
                abstract_chunks = self.chunk_text(abstract, MAX_TOKEN_LENGTH)

                if len(abstract_chunks) > 1:
                    self.stats['chunks_created'] += len(abstract_chunks) - 1

                # Process each chunk
                for i, chunk in enumerate(abstract_chunks):
                    # Create weighted embedding
                    fields = {
                        'title': title,
                        'abstract': chunk,
                        'authors': authors,
                        'categories': categories
                    }

                    embedding = self.create_weighted_embedding(fields)

                    # Store embedding and metadata
                    paper_embeddings.append(embedding)
                    paper_metadata.append({
                        'paper_id': paper.get('id', ''),
                        'title': title,
                        'authors': paper.get('authors', []),
                        'categories': paper.get('categories', []),
                        'published': paper.get('published', ''),
                        'chunk_index': i,
                        'total_chunks': len(abstract_chunks),
                        'abstract_preview': chunk[:200] + '...' if len(chunk) > 200 else chunk
                    })

                self.stats['papers_processed'] += 1
                self.stats['total_embeddings'] += len(abstract_chunks)
                pbar.update(1)

                # Memory management - clear cache periodically
                if self.stats['papers_processed'] % 50 == 0:
                    gc.collect()

        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.stats['memory_usage']['papers'] = {
            'initial_mb': initial_memory,
            'final_mb': final_memory,
            'used_mb': final_memory - initial_memory
        }

        return {
            'embeddings': np.array(paper_embeddings),
            'metadata': paper_metadata
        }

    def process_faculty(self, faculty: List[Dict]) -> Dict[str, Any]:
        """Process faculty profiles and create embeddings."""
        print(f"\n👥 Processing {len(faculty)} faculty profiles...")

        faculty_embeddings = []
        faculty_metadata = []

        for member in tqdm(faculty, desc="Creating faculty embeddings"):
            # Extract fields
            name = member.get('name', '')
            department = member.get('department', '')
            research_interests = ', '.join(member.get('research_interests', []))
            bio = member.get('bio', '')

            # Create combined text
            combined_text = f"{name}. {department}. Research interests: {research_interests}. {bio}"

            # Create embedding
            embedding = self.model.encode(combined_text, convert_to_numpy=True, show_progress_bar=False)

            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            faculty_embeddings.append(embedding)
            faculty_metadata.append({
                'name': name,
                'department': department,
                'research_interests': member.get('research_interests', []),
                'email': member.get('email', ''),
                'website': member.get('website', '')
            })

            self.stats['faculty_processed'] += 1
            self.stats['total_embeddings'] += 1

        return {
            'embeddings': np.array(faculty_embeddings),
            'metadata': faculty_metadata
        }

    def save_embeddings(self, embeddings_data: Dict[str, Any], name: str):
        """Save embeddings and metadata to pickle files."""
        output_file = self.output_dir / f"{name}_embeddings.pkl"

        print(f"\n💾 Saving {name} embeddings to {output_file}")

        # Add timestamp and stats
        embeddings_data['created_at'] = datetime.now().isoformat()
        embeddings_data['model'] = MODEL_NAME
        embeddings_data['dimension'] = self.model.get_sentence_embedding_dimension()

        with open(output_file, 'wb') as f:
            pickle.dump(embeddings_data, f)

        file_size = output_file.stat().st_size / (1024 * 1024)  # MB
        print(f"   ✅ Saved ({file_size:.2f} MB)")

        return output_file

    def estimate_vector_db_size(self, embeddings: np.ndarray) -> Dict[str, Any]:
        """Estimate vector database sizing needs."""
        num_vectors = embeddings.shape[0]
        dimension = embeddings.shape[1]

        # Calculate sizes for different index types
        flat_size = num_vectors * dimension * 4  # 4 bytes per float32
        hnsw_size = flat_size * 1.5  # HNSW index overhead ~50%
        ivf_size = flat_size * 1.2  # IVF index overhead ~20%

        estimates = {
            'num_vectors': num_vectors,
            'dimension': dimension,
            'memory_requirements': {
                'flat_index_mb': flat_size / (1024 * 1024),
                'hnsw_index_mb': hnsw_size / (1024 * 1024),
                'ivf_index_mb': ivf_size / (1024 * 1024)
            },
            'recommended': 'HNSW for < 1M vectors, IVF for larger',
            'opensearch_estimate': {
                'instance_type': 't3.small.search' if num_vectors < 10000 else 't3.medium.search',
                'storage_gb': max(1, int(hnsw_size / (1024 * 1024 * 1024) * 2))  # 2x for safety
            }
        }

        return estimates

    def print_summary(self):
        """Print processing summary."""
        print("\n" + "="*60)
        print("📊 EMBEDDING GENERATION SUMMARY")
        print("="*60)

        print(f"\n📈 Processing Statistics:")
        print(f"   Papers processed: {self.stats['papers_processed']}")
        print(f"   Faculty processed: {self.stats['faculty_processed']}")
        print(f"   Chunks created: {self.stats['chunks_created']}")
        print(f"   Total embeddings: {self.stats['total_embeddings']}")

        if 'papers' in self.stats['memory_usage']:
            mem = self.stats['memory_usage']['papers']
            print(f"\n💾 Memory Usage:")
            print(f"   Papers processing: {mem['used_mb']:.2f} MB")

        print(f"\n🔧 Model Information:")
        print(f"   Model: {MODEL_NAME}")
        print(f"   Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        print(f"   Device: CPU (Mac optimized)")

    def run(self):
        """Main execution method."""
        print("\n" + "="*60)
        print("🚀 Research Embeddings Generator")
        print("="*60)

        # Load model
        self.load_model()

        # Download data from S3
        print("\n📥 Downloading data from S3...")

        papers_cache = self.cache_dir / "papers.json"
        faculty_cache = self.cache_dir / "faculty.json"

        self.download_from_s3("raw-data/papers/arxiv_papers.json", papers_cache)
        self.download_from_s3("raw-data/faculty/faculty_profiles.json", faculty_cache)

        # Load data
        all_embeddings = []

        if papers_cache.exists():
            print("\n📄 Loading papers data...")
            with open(papers_cache, 'r') as f:
                papers = json.load(f)

            # Process papers
            papers_data = self.process_papers(papers)

            # Save paper embeddings
            papers_output = self.save_embeddings(papers_data, 'papers')
            all_embeddings.append(papers_data['embeddings'])

        if faculty_cache.exists():
            print("\n📄 Loading faculty data...")
            with open(faculty_cache, 'r') as f:
                faculty = json.load(f)

            # Process faculty
            faculty_data = self.process_faculty(faculty)

            # Save faculty embeddings
            faculty_output = self.save_embeddings(faculty_data, 'faculty')
            all_embeddings.append(faculty_data['embeddings'])

        # Combine all embeddings for sizing estimate
        if all_embeddings:
            combined = np.vstack(all_embeddings)

            print("\n📐 Vector Database Sizing Estimates:")
            estimates = self.estimate_vector_db_size(combined)

            print(f"   Total vectors: {estimates['num_vectors']:,}")
            print(f"   Dimension: {estimates['dimension']}")
            print(f"\n   Memory Requirements:")
            print(f"     • Flat index: {estimates['memory_requirements']['flat_index_mb']:.2f} MB")
            print(f"     • HNSW index: {estimates['memory_requirements']['hnsw_index_mb']:.2f} MB")
            print(f"     • IVF index: {estimates['memory_requirements']['ivf_index_mb']:.2f} MB")
            print(f"\n   OpenSearch Recommendation:")
            print(f"     • Instance: {estimates['opensearch_estimate']['instance_type']}")
            print(f"     • Storage: {estimates['opensearch_estimate']['storage_gb']} GB")

        # Print summary
        self.print_summary()

        print("\n✨ Embeddings generation complete!")
        print(f"📂 Output saved to: {self.output_dir}")

        # Save statistics
        stats_file = self.output_dir / "generation_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

        print(f"📊 Statistics saved to: {stats_file}")

if __name__ == "__main__":
    generator = EmbeddingsGenerator(use_cache=True)
    generator.run()