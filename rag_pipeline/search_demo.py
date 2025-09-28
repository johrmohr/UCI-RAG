#!/usr/bin/env python3
"""
Search-only demo (no LLM required)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag_pipeline.rag_system import RAGPipeline


def search_demo():
    """Demo search functionality"""
    print("\n" + "=" * 80)
    print("UCI RESEARCH SEARCH - Working Demo")
    print("=" * 80)

    pipeline = RAGPipeline()

    queries = [
        "quantum computing algorithms",
        "machine learning applications",
        "condensed matter physics"
    ]

    for query in queries:
        print(f"\n\n🔍 QUERY: {query}")
        print("-" * 60)

        # Search papers
        papers = pipeline.search_papers(query, top_k=3)
        print("\n📄 RELEVANT PAPERS:")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:2]) if paper['authors'] else 'N/A'}")
            print(f"   Score: {paper['relevance_score']:.3f}")
            print(f"   Preview: {paper['abstract'][:150]}...")

        # Search faculty
        faculty = pipeline.search_faculty(query, top_k=2)
        print("\n👥 RELEVANT FACULTY:")
        for i, member in enumerate(faculty, 1):
            print(f"\n{i}. {member['name']} - {member['department']}")
            if member['research_areas']:
                print(f"   Research: {', '.join(member['research_areas'][:3])}")
            print(f"   Score: {member['relevance_score']:.3f}")


if __name__ == "__main__":
    search_demo()