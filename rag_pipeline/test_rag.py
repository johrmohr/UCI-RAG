#!/usr/bin/env python3
"""
Test script for RAG system without AWS dependencies
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag_pipeline.rag_system import RAGPipeline


def test_search_only():
    """Test search functionality without LLM generation"""
    print("\n" + "=" * 80)
    print("TESTING RAG SYSTEM - SEARCH ONLY MODE")
    print("=" * 80)

    # Initialize pipeline (will work even without AWS creds)
    pipeline = RAGPipeline()

    # Test queries
    test_queries = [
        "quantum computing algorithms",
        "condensed matter physics",
        "superconductors and quantum materials"
    ]

    for query in test_queries:
        print(f"\n\nQUERY: {query}")
        print("-" * 40)

        # Search papers
        papers = pipeline.search_papers(query, top_k=3)
        print(f"\nFound {len(papers)} papers:")
        for i, paper in enumerate(papers, 1):
            print(f"  {i}. {paper['title'][:60]}...")
            print(f"     Relevance: {paper['relevance_score']:.3f}")

        # Search faculty
        faculty = pipeline.search_faculty(query, top_k=2)
        print(f"\nFound {len(faculty)} faculty:")
        for i, member in enumerate(faculty, 1):
            print(f"  {i}. {member['name']} - {member['department']}")
            print(f"     Relevance: {member['relevance_score']:.3f}")


def test_full_pipeline():
    """Test full pipeline with mock responses if AWS is unavailable"""
    print("\n" + "=" * 80)
    print("TESTING FULL RAG PIPELINE")
    print("=" * 80)

    pipeline = RAGPipeline()

    # Single test query
    query = "What research is happening in quantum computing at UCI?"
    result = pipeline.generate_answer(query)

    # Display results
    print(f"\nQuery: {query}")
    print("\n" + "-" * 40)
    print("ANSWER:")
    print("-" * 40)
    print(result['answer'])

    print("\n" + "-" * 40)
    print(f"Papers found: {len(result['papers'])}")
    for paper in result['papers'][:3]:
        print(f"  - {paper['title'][:60]}...")

    print(f"\nFaculty found: {len(result['faculty'])}")
    for member in result['faculty']:
        print(f"  - {member['name']} ({member['department']})")

    print("\n" + "-" * 40)
    print(f"Status: {result['status']}")
    print(f"Estimated cost: ${result['estimated_cost']:.6f}")


if __name__ == "__main__":
    print("Running RAG System Tests...")
    print("\n1. Testing Search Functionality:")
    test_search_only()

    print("\n\n2. Testing Full Pipeline:")
    test_full_pipeline()

    print("\n\n✅ All tests completed!")