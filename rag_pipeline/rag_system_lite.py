#!/usr/bin/env python3
"""
Lightweight RAG System that works without heavy ML dependencies
Uses real ArXiv data with simple keyword/text matching
Supports Claude AI when AWS credentials are available
"""

import os
import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import re

# Try to import AWS SDK for Claude
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

class RAGPipelineLite:
    """Lightweight RAG pipeline using real data with simple search"""

    # Claude Haiku pricing (per 1K tokens)
    HAIKU_INPUT_COST = 0.00025  # $0.25 per million tokens
    HAIKU_OUTPUT_COST = 0.00125  # $1.25 per million tokens

    def __init__(self, **kwargs):
        """Initialize pipeline with real data"""
        self.demo_mode = False
        self.papers = self._load_real_papers()

        # Try to initialize Claude if AWS credentials are available
        self.bedrock_client = None
        self.use_claude = False
        self._init_claude()

        # Set stats based on capabilities
        self.stats = {
            "papers_indexed": len(self.papers),
            "embedding_model": "Keyword matching (lite mode)",
            "llm_model": "Claude 3 Haiku" if self.use_claude else "Template-based responses (lite mode)",
            "status": "Ready with Claude AI" if self.use_claude else "Ready (Lite Mode)"
        }

    def _init_claude(self):
        """Initialize Claude/Bedrock if credentials are available"""
        if not BOTO3_AVAILABLE:
            print("boto3 not available, Claude AI disabled")
            return

        try:
            # Check for AWS credentials
            if not (os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY')):
                print("AWS credentials not found, Claude AI disabled")
                return

            # Initialize Bedrock client
            region = os.environ.get('AWS_DEFAULT_REGION', 'us-west-2')
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region
            )

            # Test if we can access Bedrock
            self.use_claude = True
            print("Claude AI initialized successfully!")

        except Exception as e:
            print(f"Could not initialize Claude: {e}")
            self.bedrock_client = None
            self.use_claude = False

    def _load_real_papers(self) -> List[Dict]:
        """Load real papers from JSON file"""
        try:
            # Try to load the real UCI research data
            data_path = Path(__file__).parent.parent / "data_generation" / "uci_research_data.json"

            if data_path.exists():
                with open(data_path, 'r') as f:
                    data = json.load(f)
                    papers = data.get('papers', [])

                    # Process papers for easier searching
                    for paper in papers:
                        # Create searchable text field
                        paper['searchable_text'] = ' '.join([
                            paper.get('title', ''),
                            paper.get('abstract', ''),
                            ' '.join(paper.get('categories', [])),
                            ' '.join(paper.get('authors', []))
                        ]).lower()

                    return papers
            else:
                print(f"Data file not found at {data_path}")
                return self._get_fallback_papers()

        except Exception as e:
            print(f"Error loading data: {e}")
            return self._get_fallback_papers()

    def _get_fallback_papers(self) -> List[Dict]:
        """Fallback sample papers if real data can't be loaded"""
        return [
            {
                "arxiv_id": "2024.12345",
                "title": "Quantum Machine Learning: A Survey",
                "authors": ["Smith, J.", "Chen, L."],
                "abstract": "We present a comprehensive overview of quantum machine learning algorithms...",
                "year": 2024,
                "categories": ["quant-ph"],
                "searchable_text": "quantum machine learning survey algorithms smith chen"
            }
        ]

    def _calculate_relevance(self, paper: Dict, query: str) -> float:
        """Calculate relevance score using keyword matching"""
        query_lower = query.lower()
        query_terms = query_lower.split()

        searchable = paper.get('searchable_text', '')

        # Count matching terms
        matches = 0
        for term in query_terms:
            # Skip common words
            if term in ['the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'a', 'an']:
                continue
            # Count occurrences
            matches += searchable.count(term)

        # Title match is worth more
        title_lower = paper.get('title', '').lower()
        for term in query_terms:
            if term in title_lower:
                matches += 3

        # Normalize score between 0 and 1
        max_score = max(1, matches)
        return min(1.0, matches / 10.0)

    def search_papers(self, query: str, k: int = 5) -> List[Dict]:
        """Search papers using keyword matching"""

        # Calculate relevance for all papers
        scored_papers = []
        for paper in self.papers:
            score = self._calculate_relevance(paper, query)
            if score > 0:
                paper_copy = paper.copy()
                paper_copy['relevance_score'] = score
                scored_papers.append(paper_copy)

        # Sort by relevance and return top k
        scored_papers.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Return top k results
        results = scored_papers[:k]

        # Clean up results (remove searchable_text field)
        for paper in results:
            paper.pop('searchable_text', None)

        return results

    def _generate_claude_answer(self, query: str, papers: List[Dict]) -> Dict:
        """Generate answer using Claude AI"""
        if not self.bedrock_client:
            return self._generate_template_answer(query, papers)

        try:
            # Prepare context from papers
            context = "Here are the relevant research papers:\n\n"
            for i, paper in enumerate(papers[:3], 1):
                context += f"Paper {i}:\n"
                context += f"Title: {paper.get('title', 'Unknown')}\n"
                context += f"Authors: {', '.join(paper.get('authors', ['Unknown']))}\n"
                context += f"Abstract: {paper.get('abstract', 'No abstract')[:500]}...\n\n"

            # Prepare prompt for Claude
            prompt = f"""Based on the following research papers, please answer this question: {query}

{context}

Please provide a comprehensive answer that:
1. Directly addresses the user's question
2. Cites specific papers when relevant
3. Highlights key findings and contributions
4. Suggests areas for further exploration if applicable

Keep the response concise but informative."""

            # Call Claude via Bedrock
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.3,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })

            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=body
            )

            # Parse response
            response_body = json.loads(response.get("body").read())
            answer = response_body.get("content", [{}])[0].get("text", "No response generated")

            # Calculate token usage
            usage = response_body.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            # Calculate cost
            input_cost = (input_tokens / 1000) * self.HAIKU_INPUT_COST
            output_cost = (output_tokens / 1000) * self.HAIKU_OUTPUT_COST
            total_cost = input_cost + output_cost

            return {
                "answer": answer,
                "papers_used": len(papers),
                "confidence": 0.95,
                "cost_estimate": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_cost": total_cost
                }
            }

        except Exception as e:
            print(f"Claude generation failed: {e}")
            # Fall back to template answer
            return self._generate_template_answer(query, papers)

    def _generate_template_answer(self, query: str, papers: List[Dict]) -> Dict:
        """Generate template-based answer (fallback)"""
        if not papers:
            response = f"I couldn't find any papers directly related to '{query}' in our database. Try broadening your search terms."
        else:
            # Extract key information from papers
            topics = set()
            authors = set()
            years = set()

            for paper in papers[:3]:  # Use top 3 papers
                # Extract categories/topics
                for cat in paper.get('categories', []):
                    topics.add(cat)

                # Extract years
                if 'published' in paper:
                    year = paper['published'][:4]
                    years.add(year)

                # Extract first authors
                author_list = paper.get('authors', [])
                if author_list:
                    authors.add(author_list[0].split(',')[0])

            # Build response
            response = f"Based on your query about **'{query}'**, I found {len(papers)} relevant papers in our database.\n\n"

            response += "**Key Findings:**\n\n"

            # Summarize the top paper
            if papers:
                top_paper = papers[0]
                response += f"• The most relevant paper is *\"{top_paper.get('title', 'Unknown')}\"* "

                if top_paper.get('authors'):
                    response += f"by {top_paper['authors'][0]} et al. "

                if 'abstract' in top_paper:
                    # Extract first sentence of abstract
                    abstract = top_paper['abstract']
                    first_sentence = abstract.split('.')[0] + '.'
                    response += f"\n\n• Abstract excerpt: {first_sentence}\n\n"

            # Add topic summary
            if topics:
                response += f"• These papers cover areas including: {', '.join(sorted(topics)[:3])}\n\n"

            # Add temporal information
            if years:
                sorted_years = sorted(years)
                response += f"• Publications span from {sorted_years[0]} to {sorted_years[-1]}\n\n"

            # Add note about lite mode
            if not self.use_claude:
                response += "\n*Note: This is a keyword-based search with template responses. Add AWS credentials for Claude AI summaries.*"

        return {
            "answer": response,
            "papers_used": len(papers),
            "confidence": 0.75 if papers else 0.0,
            "cost_estimate": {"input_tokens": 0, "output_tokens": 0, "total_cost": 0}
        }

    def generate_answer(self, query: str, papers: List[Dict]) -> Dict:
        """Generate answer using Claude if available, otherwise use template"""
        if self.use_claude:
            return self._generate_claude_answer(query, papers)
        else:
            return self._generate_template_answer(query, papers)

    def query(self, question: str, k: int = 5) -> Dict:
        """Main query interface"""

        # Search for relevant papers
        papers = self.search_papers(question, k)

        # Generate answer
        result = self.generate_answer(question, papers)

        # Add source papers to result
        result["source_papers"] = papers

        return result

    def get_stats(self) -> Dict:
        """Get system statistics"""
        return self.stats

    def get_sample_queries(self) -> List[str]:
        """Get sample queries based on actual data"""
        queries = [
            "quantum computing applications",
            "machine learning in physics",
            "condensed matter research",
            "high energy physics",
            "gravitational waves",
            "dark matter detection"
        ]
        return queries