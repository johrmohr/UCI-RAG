#!/usr/bin/env python3
"""
ChromaDB Setup for UCI Research Intelligence
Indexes embeddings and provides multiple search methods
"""

import os
import sys
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

try:
    import chromadb
    from chromadb.utils import embedding_functions
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB not installed. Installing...")
    os.system("pip install chromadb")
    import chromadb
    from chromadb.utils import embedding_functions
    from chromadb.config import Settings

import numpy as np
from tqdm import tqdm


class UCIResearchDatabase:
    """ChromaDB wrapper for UCI research data"""

    def __init__(self, persist_directory: str = "chroma_db", reset: bool = False):
        """
        Initialize ChromaDB client and collections

        Args:
            persist_directory: Directory to persist the database
            reset: Whether to reset existing database
        """
        self.persist_directory = Path(persist_directory)

        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        if reset:
            print("Resetting database...")
            self.client.reset()

        # Initialize collections
        self._init_collections()

    def _init_collections(self):
        """Initialize or get collections for papers and faculty"""
        try:
            # Papers collection
            self.papers_collection = self.client.get_or_create_collection(
                name="uci_papers",
                metadata={"description": "UCI research papers and publications"}
            )

            # Faculty collection
            self.faculty_collection = self.client.get_or_create_collection(
                name="uci_faculty",
                metadata={"description": "UCI faculty profiles and research areas"}
            )

            print(f"Collections initialized:")
            print(f"  - Papers: {self.papers_collection.name}")
            print(f"  - Faculty: {self.faculty_collection.name}")

        except Exception as e:
            print(f"Error initializing collections: {e}")
            raise

    def _generate_id(self, text: str, prefix: str = "") -> str:
        """Generate unique ID for documents"""
        hash_obj = hashlib.md5(text.encode())
        return f"{prefix}_{hash_obj.hexdigest()[:12]}"

    def load_embeddings(self, embeddings_dir: str = "embeddings/output") -> Tuple[Dict, Dict]:
        """
        Load embeddings from pickle files

        Returns:
            Tuple of (papers_data, faculty_data) dictionaries
        """
        embeddings_path = Path(embeddings_dir)
        papers_data = {}
        faculty_data = {}

        print(f"\nLoading embeddings from {embeddings_path}...")

        # Load paper embeddings
        papers_file = embeddings_path / "papers_embeddings.pkl"
        if papers_file.exists():
            with open(papers_file, 'rb') as f:
                raw_data = pickle.load(f)
                # Handle new format with embeddings and metadata
                if isinstance(raw_data, dict) and 'embeddings' in raw_data and 'metadata' in raw_data:
                    embeddings = raw_data['embeddings']
                    metadata_list = raw_data['metadata']
                    # Convert to expected format
                    for i, meta in enumerate(metadata_list):
                        # Generate unique ID if paper_id is empty or missing
                        paper_id = meta.get('paper_id', '').strip()
                        if not paper_id:
                            # Use title and index for unique ID
                            title = meta.get('title', f'Untitled_{i}')
                            paper_id = f"{title[:50]}_{i}"
                        papers_data[paper_id] = {
                            'embedding': embeddings[i],
                            'title': meta.get('title', ''),
                            'authors': meta.get('authors', []),
                            'abstract': meta.get('abstract_preview', ''),
                            'year': int(meta.get('published', '2023')[:4]) if meta.get('published') else 2023,
                            'venue': '',
                            'citations': 0,
                            'url': '',
                            'category': meta.get('categories', [''])[0] if meta.get('categories') else ''
                        }
                else:
                    papers_data = raw_data
            print(f"  Loaded {len(papers_data)} paper embeddings")

        # Load faculty embeddings
        faculty_file = embeddings_path / "faculty_embeddings.pkl"
        if faculty_file.exists():
            with open(faculty_file, 'rb') as f:
                raw_data = pickle.load(f)
                # Handle new format with embeddings and metadata
                if isinstance(raw_data, dict) and 'embeddings' in raw_data and 'metadata' in raw_data:
                    embeddings = raw_data['embeddings']
                    metadata_list = raw_data['metadata']
                    # Convert to expected format
                    for i, meta in enumerate(metadata_list):
                        faculty_name = meta.get('name', f'faculty_{i}')
                        faculty_data[faculty_name] = {
                            'embedding': embeddings[i],
                            'department': meta.get('department', ''),
                            'title': meta.get('title', ''),
                            'email': meta.get('email', ''),
                            'phone': '',
                            'office': '',
                            'website': meta.get('profile_url', ''),
                            'research_areas': meta.get('research_areas', []),
                            'bio': meta.get('bio_preview', '')
                        }
                else:
                    faculty_data = raw_data
            print(f"  Loaded {len(faculty_data)} faculty embeddings")

        return papers_data, faculty_data

    def index_papers(self, papers_data: Dict) -> int:
        """
        Index paper embeddings into ChromaDB

        Returns:
            Number of papers indexed
        """
        if not papers_data:
            print("No papers to index")
            return 0

        print(f"\nIndexing {len(papers_data)} papers...")

        # Prepare batch data
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for paper_id, paper_info in tqdm(papers_data.items(), desc="Preparing papers"):
            # Generate unique ID
            doc_id = self._generate_id(paper_id, "paper")
            ids.append(doc_id)

            # Extract embedding
            embedding = paper_info.get('embedding')
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            embeddings.append(embedding)

            # Prepare metadata
            metadata = {
                'original_id': paper_id,
                'title': paper_info.get('title', ''),
                'authors': json.dumps(paper_info.get('authors', [])),
                'year': paper_info.get('year', 0),
                'venue': paper_info.get('venue', ''),
                'citations': paper_info.get('citations', 0),
                'url': paper_info.get('url', ''),
                'category': paper_info.get('category', 'research'),
                'indexed_at': datetime.now().isoformat()
            }
            metadatas.append(metadata)

            # Create document text for hybrid search
            abstract = paper_info.get('abstract', '')
            title = paper_info.get('title', '')
            doc_text = f"{title}\n\n{abstract}"
            documents.append(doc_text)

        # Batch upsert to ChromaDB
        try:
            self.papers_collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            print(f"Successfully indexed {len(ids)} papers")
            return len(ids)
        except Exception as e:
            print(f"Error indexing papers: {e}")
            return 0

    def index_faculty(self, faculty_data: Dict) -> int:
        """
        Index faculty embeddings into ChromaDB

        Returns:
            Number of faculty profiles indexed
        """
        if not faculty_data:
            print("No faculty to index")
            return 0

        print(f"\nIndexing {len(faculty_data)} faculty profiles...")

        # Prepare batch data
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for faculty_name, faculty_info in tqdm(faculty_data.items(), desc="Preparing faculty"):
            # Generate unique ID
            doc_id = self._generate_id(faculty_name, "faculty")
            ids.append(doc_id)

            # Extract embedding
            embedding = faculty_info.get('embedding')
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            embeddings.append(embedding)

            # Prepare metadata
            metadata = {
                'name': faculty_name,
                'department': faculty_info.get('department', ''),
                'title': faculty_info.get('title', ''),
                'email': faculty_info.get('email', ''),
                'phone': faculty_info.get('phone', ''),
                'office': faculty_info.get('office', ''),
                'website': faculty_info.get('website', ''),
                'research_areas': json.dumps(faculty_info.get('research_areas', [])),
                'indexed_at': datetime.now().isoformat()
            }
            metadatas.append(metadata)

            # Create document text for hybrid search
            research = ' '.join(faculty_info.get('research_areas', []))
            bio = faculty_info.get('bio', '')
            doc_text = f"{faculty_name}\n{faculty_info.get('title', '')}\n{faculty_info.get('department', '')}\n\nResearch Areas: {research}\n\n{bio}"
            documents.append(doc_text)

        # Batch upsert to ChromaDB
        try:
            self.faculty_collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            print(f"Successfully indexed {len(ids)} faculty profiles")
            return len(ids)
        except Exception as e:
            print(f"Error indexing faculty: {e}")
            return 0

    def semantic_search(self,
                       query_embedding: List[float],
                       collection: str = "papers",
                       n_results: int = 10) -> Dict:
        """
        Perform semantic similarity search using embeddings

        Args:
            query_embedding: Query embedding vector
            collection: Which collection to search ("papers" or "faculty")
            n_results: Number of results to return

        Returns:
            Search results with metadata
        """
        target_collection = (self.papers_collection if collection == "papers"
                           else self.faculty_collection)

        results = target_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return self._format_results(results)

    def hybrid_search(self,
                     query_text: str,
                     query_embedding: Optional[List[float]] = None,
                     collection: str = "papers",
                     n_results: int = 10,
                     alpha: float = 0.5) -> Dict:
        """
        Perform hybrid search combining keyword and semantic search

        Args:
            query_text: Text query for keyword matching
            query_embedding: Optional embedding for semantic search
            collection: Which collection to search
            n_results: Number of results
            alpha: Weight for semantic vs keyword (0=keyword only, 1=semantic only)

        Returns:
            Combined search results
        """
        target_collection = (self.papers_collection if collection == "papers"
                           else self.faculty_collection)

        results = {}

        # Keyword search
        if alpha < 1.0:
            keyword_results = target_collection.query(
                query_texts=[query_text],
                n_results=n_results * 2  # Get more for merging
            )
            results['keyword'] = self._format_results(keyword_results)

        # Semantic search
        if query_embedding and alpha > 0.0:
            semantic_results = target_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2
            )
            results['semantic'] = self._format_results(semantic_results)

        # Merge and rank results
        if 'keyword' in results and 'semantic' in results:
            merged = self._merge_results(
                results['keyword'],
                results['semantic'],
                alpha,
                n_results
            )
            results['merged'] = merged

        return results

    def filtered_search(self,
                       query_embedding: Optional[List[float]] = None,
                       query_text: Optional[str] = None,
                       collection: str = "papers",
                       filters: Dict[str, Any] = None,
                       n_results: int = 10) -> Dict:
        """
        Search with metadata filters

        Args:
            query_embedding: Optional embedding for semantic search
            query_text: Optional text for keyword search
            collection: Which collection to search
            filters: Metadata filters (e.g., {"year": 2023, "department": "Computer Science"})
            n_results: Number of results

        Returns:
            Filtered search results
        """
        target_collection = (self.papers_collection if collection == "papers"
                           else self.faculty_collection)

        # Build where clause for filtering
        where_clause = {}
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    where_clause[key] = {"$in": value}
                else:
                    where_clause[key] = value

        # Perform search
        if query_embedding:
            results = target_collection.query(
                query_embeddings=[query_embedding],
                where=where_clause if where_clause else None,
                n_results=n_results
            )
        elif query_text:
            results = target_collection.query(
                query_texts=[query_text],
                where=where_clause if where_clause else None,
                n_results=n_results
            )
        else:
            # Just filter without search
            results = target_collection.get(
                where=where_clause if where_clause else None,
                limit=n_results
            )
            # Format get results to match query format
            results = {
                'ids': [[results.get('ids', [])]],
                'metadatas': [[results.get('metadatas', [])]],
                'documents': [[results.get('documents', [])]],
                'distances': [[]]
            }

        return self._format_results(results)

    def _format_results(self, results: Dict) -> Dict:
        """Format ChromaDB results for easier use"""
        formatted = {
            'results': [],
            'count': 0
        }

        if results and 'ids' in results and results['ids']:
            ids = results['ids'][0] if results['ids'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            documents = results['documents'][0] if results['documents'] else []
            distances = results['distances'][0] if 'distances' in results and results['distances'] else []

            for i in range(len(ids)):
                result_item = {
                    'id': ids[i],
                    'metadata': metadatas[i] if i < len(metadatas) else {},
                    'document': documents[i] if i < len(documents) else "",
                    'distance': distances[i] if i < len(distances) else None
                }

                # Parse JSON fields in metadata
                if 'authors' in result_item['metadata']:
                    try:
                        result_item['metadata']['authors'] = json.loads(
                            result_item['metadata']['authors']
                        )
                    except:
                        pass

                if 'research_areas' in result_item['metadata']:
                    try:
                        result_item['metadata']['research_areas'] = json.loads(
                            result_item['metadata']['research_areas']
                        )
                    except:
                        pass

                formatted['results'].append(result_item)

            formatted['count'] = len(formatted['results'])

        return formatted

    def _merge_results(self, keyword_results: Dict, semantic_results: Dict,
                      alpha: float, n_results: int) -> List[Dict]:
        """Merge keyword and semantic search results with weighting"""
        # Create score maps
        keyword_scores = {}
        semantic_scores = {}

        # Normalize and store keyword scores
        for i, result in enumerate(keyword_results.get('results', [])):
            doc_id = result['id']
            # Inverse rank scoring for keyword results
            keyword_scores[doc_id] = 1.0 / (i + 1)

        # Normalize and store semantic scores
        for i, result in enumerate(semantic_results.get('results', [])):
            doc_id = result['id']
            # Use distance for scoring (lower distance = higher score)
            distance = result.get('distance', 1.0)
            semantic_scores[doc_id] = 1.0 / (distance + 0.001)

        # Combine scores
        all_ids = set(keyword_scores.keys()) | set(semantic_scores.keys())
        combined_scores = {}

        for doc_id in all_ids:
            keyword_score = keyword_scores.get(doc_id, 0)
            semantic_score = semantic_scores.get(doc_id, 0)
            combined_scores[doc_id] = (1 - alpha) * keyword_score + alpha * semantic_score

        # Sort by combined score
        sorted_ids = sorted(combined_scores.keys(),
                          key=lambda x: combined_scores[x],
                          reverse=True)[:n_results]

        # Build merged results
        merged = []
        all_results = {r['id']: r for r in keyword_results.get('results', [])}
        all_results.update({r['id']: r for r in semantic_results.get('results', [])})

        for doc_id in sorted_ids:
            if doc_id in all_results:
                result = all_results[doc_id].copy()
                result['combined_score'] = combined_scores[doc_id]
                merged.append(result)

        return merged

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {
            'database_path': str(self.persist_directory),
            'collections': {},
            'total_documents': 0
        }

        # Papers statistics
        papers_count = self.papers_collection.count()
        stats['collections']['papers'] = {
            'count': papers_count,
            'name': self.papers_collection.name
        }

        # Faculty statistics
        faculty_count = self.faculty_collection.count()
        stats['collections']['faculty'] = {
            'count': faculty_count,
            'name': self.faculty_collection.name
        }

        stats['total_documents'] = papers_count + faculty_count

        return stats


def main():
    """Main function to set up ChromaDB with UCI research data"""
    print("=" * 60)
    print("UCI Research Intelligence - ChromaDB Setup")
    print("=" * 60)

    # Initialize database
    print("\nInitializing ChromaDB...")
    db = UCIResearchDatabase(persist_directory="chroma_db", reset=True)

    # Load embeddings
    papers_data, faculty_data = db.load_embeddings("embeddings/output")

    # Index data
    papers_indexed = db.index_papers(papers_data)
    faculty_indexed = db.index_faculty(faculty_data)

    # Show statistics
    print("\n" + "=" * 60)
    print("Indexing Complete!")
    print("=" * 60)

    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Location: {stats['database_path']}")
    print(f"  Total Documents: {stats['total_documents']}")
    print(f"\nCollections:")
    for name, info in stats['collections'].items():
        print(f"  - {name}: {info['count']} documents")

    # Test searches
    print("\n" + "=" * 60)
    print("Testing Search Methods")
    print("=" * 60)

    # Test with a sample embedding (using first paper's embedding)
    if papers_data:
        sample_key = list(papers_data.keys())[0]
        sample_embedding = papers_data[sample_key]['embedding']
        if isinstance(sample_embedding, np.ndarray):
            sample_embedding = sample_embedding.tolist()

        # Test semantic search
        print("\n1. Testing Semantic Search (Papers)...")
        semantic_results = db.semantic_search(
            query_embedding=sample_embedding,
            collection="papers",
            n_results=5
        )
        print(f"   Found {semantic_results['count']} similar papers")
        if semantic_results['results']:
            print(f"   Top result: {semantic_results['results'][0]['metadata'].get('title', 'N/A')}")

        # Test hybrid search
        print("\n2. Testing Hybrid Search...")
        hybrid_results = db.hybrid_search(
            query_text="machine learning",
            query_embedding=sample_embedding,
            collection="papers",
            n_results=5,
            alpha=0.5
        )
        if 'merged' in hybrid_results:
            print(f"   Found {len(hybrid_results['merged'])} results")

        # Test filtered search
        print("\n3. Testing Filtered Search...")
        filtered_results = db.filtered_search(
            query_embedding=sample_embedding,
            collection="papers",
            filters={"year": 2023},
            n_results=5
        )
        print(f"   Found {filtered_results['count']} papers from 2023")

    print("\n✅ ChromaDB setup complete and operational!")
    print(f"   Database saved to: ./chroma_db/")
    print(f"   Ready for semantic search queries!")

    return db


if __name__ == "__main__":
    db = main()