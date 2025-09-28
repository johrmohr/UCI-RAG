#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) System for UCI Research Intelligence
Combines ChromaDB vector search with Amazon Bedrock's Claude Haiku for Q&A
"""

import os
import sys
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import tiktoken

# Amazon Bedrock imports
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("AWS SDK not installed. Installing boto3...")
    os.system("pip install boto3")
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError


class RAGPipeline:
    """RAG pipeline combining ChromaDB search with Claude Haiku generation"""

    # Claude Haiku pricing (per 1K tokens)
    HAIKU_INPUT_COST = 0.00025  # $0.25 per million tokens
    HAIKU_OUTPUT_COST = 0.00125  # $1.25 per million tokens

    def __init__(self,
                 chroma_path: str = None,
                 embeddings_model: str = "all-MiniLM-L6-v2",
                 aws_region: str = "us-west-2"):
        """
        Initialize RAG pipeline

        Args:
            chroma_path: Path to ChromaDB database
            embeddings_model: Model for generating embeddings
            aws_region: AWS region for Bedrock
        """
        # Auto-detect chroma_db path
        if chroma_path is None:
            # Try to find chroma_db in parent directory structure
            current_path = Path(__file__).parent
            possible_paths = [
                current_path / "chroma_db",
                current_path.parent / "chroma_db",
                current_path.parent / "embeddings" / "chroma_db",
                Path.cwd() / "chroma_db"
            ]
            for path in possible_paths:
                if path.exists():
                    self.chroma_path = path
                    break
            else:
                raise FileNotFoundError(f"ChromaDB not found. Searched in: {[str(p) for p in possible_paths]}")
        else:
            self.chroma_path = Path(chroma_path)

        self.aws_region = aws_region

        # Initialize embeddings model
        print("Loading embeddings model...")
        self.embeddings_model = SentenceTransformer(embeddings_model)

        # Initialize ChromaDB client
        self._init_chromadb()

        # Initialize Amazon Bedrock client
        self._init_bedrock()

        # Token counter for cost estimation
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _init_chromadb(self):
        """Initialize ChromaDB client and collections"""
        print(f"Connecting to ChromaDB at {self.chroma_path}...")

        if not self.chroma_path.exists():
            raise FileNotFoundError(f"ChromaDB not found at {self.chroma_path}")

        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get collections
        try:
            self.papers_collection = self.chroma_client.get_collection("uci_papers")
            self.faculty_collection = self.chroma_client.get_collection("uci_faculty")
            print(f"  Connected to collections: papers ({self.papers_collection.count()} docs), "
                  f"faculty ({self.faculty_collection.count()} docs)")
        except Exception as e:
            print(f"Error loading collections: {e}")
            raise

    def _init_bedrock(self):
        """Initialize Amazon Bedrock client"""
        try:
            print("Initializing Amazon Bedrock...")
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.aws_region
            )
            print(f"  Connected to Bedrock in {self.aws_region}")
        except NoCredentialsError:
            print("\n⚠️  AWS credentials not configured!")
            print("Please configure AWS credentials using:")
            print("  - AWS CLI: aws configure")
            print("  - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            print("  - IAM role (if on EC2)")
            print("\nProceeding without LLM generation (search-only mode)...")
            self.bedrock = None

    def search_papers(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant research papers

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant papers with metadata
        """
        # Generate query embedding
        query_embedding = self.embeddings_model.encode(query).tolist()

        # Search in ChromaDB
        results = self.papers_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['metadatas', 'documents', 'distances']
        )

        # Format results
        papers = []
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                paper = {
                    'id': results['ids'][0][i],
                    'title': results['metadatas'][0][i].get('title', 'Untitled'),
                    'authors': json.loads(results['metadatas'][0][i].get('authors', '[]')),
                    'year': results['metadatas'][0][i].get('year', 'N/A'),
                    'abstract': results['documents'][0][i][:500] + '...' if len(results['documents'][0][i]) > 500 else results['documents'][0][i],
                    'relevance_score': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    'venue': results['metadatas'][0][i].get('venue', ''),
                    'category': results['metadatas'][0][i].get('category', '')
                }
                papers.append(paper)

        return papers

    def search_faculty(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for relevant faculty members

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant faculty with metadata
        """
        # Generate query embedding
        query_embedding = self.embeddings_model.encode(query).tolist()

        # Search in ChromaDB
        results = self.faculty_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['metadatas', 'documents', 'distances']
        )

        # Format results
        faculty = []
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                member = {
                    'name': results['metadatas'][0][i].get('name', 'Unknown'),
                    'department': results['metadatas'][0][i].get('department', ''),
                    'title': results['metadatas'][0][i].get('title', ''),
                    'research_areas': json.loads(results['metadatas'][0][i].get('research_areas', '[]')),
                    'email': results['metadatas'][0][i].get('email', ''),
                    'bio': results['documents'][0][i][:300] + '...' if len(results['documents'][0][i]) > 300 else results['documents'][0][i],
                    'relevance_score': 1.0 - results['distances'][0][i]
                }
                faculty.append(member)

        return faculty

    def _create_context(self, papers: List[Dict], faculty: List[Dict]) -> str:
        """Create context string from search results"""
        context = ""

        if papers:
            context += "## Relevant Research Papers:\n\n"
            for i, paper in enumerate(papers, 1):
                context += f"{i}. **{paper['title']}**\n"
                if paper['authors']:
                    context += f"   Authors: {', '.join(paper['authors'][:3])}"
                    if len(paper['authors']) > 3:
                        context += f" et al."
                    context += "\n"
                context += f"   Year: {paper['year']}\n"
                context += f"   Abstract: {paper['abstract']}\n"
                context += f"   Relevance: {paper['relevance_score']:.2f}\n\n"

        if faculty:
            context += "\n## Relevant Faculty Members:\n\n"
            for i, member in enumerate(faculty, 1):
                context += f"{i}. **{member['name']}**\n"
                context += f"   {member['title']}, {member['department']}\n"
                if member['research_areas']:
                    context += f"   Research Areas: {', '.join(member['research_areas'][:3])}\n"
                context += f"   Bio: {member['bio']}\n"
                context += f"   Relevance: {member['relevance_score']:.2f}\n\n"

        return context

    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for Claude Haiku"""
        prompt = f"""You are an AI research assistant with expertise in academic literature and research at UC Irvine.

Based on the following search results from the UCI research database, provide a comprehensive and accurate answer to the user's query.

IMPORTANT INSTRUCTIONS:
1. Base your answer primarily on the provided context
2. Cite specific papers and faculty when relevant using [Author et al., Year] format
3. If the context doesn't contain enough information, acknowledge this limitation
4. Be concise but thorough (aim for 200-400 words)
5. Use academic language appropriate for researchers
6. Highlight key findings, methodologies, or contributions when relevant

SEARCH CONTEXT:
{context}

USER QUERY: {query}

RESPONSE:"""

        return prompt

    def _call_claude_haiku(self, prompt: str) -> Tuple[str, int, int]:
        """
        Call Claude Haiku via Amazon Bedrock

        Returns:
            Tuple of (response text, input tokens, output tokens)
        """
        if not self.bedrock:
            return "LLM generation unavailable (AWS credentials not configured). Showing search results only.", 0, 0

        try:
            # Prepare the request
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more focused answers
                "top_p": 0.9,
                "top_k": 50
            })

            # Call Claude 3 Haiku
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=body,
                contentType='application/json',
                accept='application/json'
            )

            # Parse response
            result = json.loads(response['body'].read())
            answer = result['content'][0]['text']

            # Estimate tokens (Bedrock doesn't always return exact counts)
            input_tokens = len(self.tokenizer.encode(prompt))
            output_tokens = len(self.tokenizer.encode(answer))

            return answer, input_tokens, output_tokens

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                return "Access denied to Claude Haiku. Please check your AWS IAM permissions for Bedrock.", 0, 0
            elif error_code == 'ResourceNotFoundException':
                return "Claude Haiku model not available in this region. Try us-west-2 or us-east-1.", 0, 0
            else:
                return f"Error calling Claude: {str(e)}", 0, 0
        except Exception as e:
            return f"Unexpected error: {str(e)}", 0, 0

    def generate_answer(self, query: str,
                       search_papers: bool = True,
                       search_faculty: bool = True,
                       paper_top_k: int = 5,
                       faculty_top_k: int = 3) -> Dict[str, Any]:
        """
        Generate answer using RAG pipeline

        Args:
            query: User question
            search_papers: Whether to search papers
            search_faculty: Whether to search faculty
            paper_top_k: Number of papers to retrieve
            faculty_top_k: Number of faculty to retrieve

        Returns:
            Dict with answer, sources, and metadata
        """
        print(f"\n🔍 Processing query: '{query}'")

        # Step 1: Retrieve relevant documents
        papers = []
        faculty = []

        if search_papers:
            print("  Searching papers...")
            papers = self.search_papers(query, paper_top_k)
            print(f"    Found {len(papers)} relevant papers")

        if search_faculty:
            print("  Searching faculty...")
            faculty = self.search_faculty(query, faculty_top_k)
            print(f"    Found {len(faculty)} relevant faculty")

        # Handle no results case
        if not papers and not faculty:
            return {
                'answer': "No relevant results found in the database for your query. Please try rephrasing or using different keywords.",
                'papers': [],
                'faculty': [],
                'input_tokens': 0,
                'output_tokens': 0,
                'estimated_cost': 0.0,
                'status': 'no_results'
            }

        # Step 2: Create context and prompt
        context = self._create_context(papers, faculty)
        prompt = self._create_prompt(query, context)

        # Step 3: Generate answer with Claude Haiku
        print("  Generating answer with Claude Haiku...")
        answer, input_tokens, output_tokens = self._call_claude_haiku(prompt)

        # Update token counts
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        # Calculate cost
        cost = self._calculate_cost(input_tokens, output_tokens)

        return {
            'answer': answer,
            'papers': papers,
            'faculty': faculty,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'estimated_cost': cost,
            'status': 'success'
        }

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost in USD"""
        input_cost = (input_tokens / 1000) * self.HAIKU_INPUT_COST
        output_cost = (output_tokens / 1000) * self.HAIKU_OUTPUT_COST
        return input_cost + output_cost

    def get_total_cost(self) -> Dict[str, float]:
        """Get total cost for the session"""
        total_cost = self._calculate_cost(self.total_input_tokens, self.total_output_tokens)
        return {
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_cost_usd': total_cost,
            'input_cost_usd': (self.total_input_tokens / 1000) * self.HAIKU_INPUT_COST,
            'output_cost_usd': (self.total_output_tokens / 1000) * self.HAIKU_OUTPUT_COST
        }

    def format_response(self, result: Dict[str, Any]) -> str:
        """Format response for display"""
        output = []
        output.append("=" * 80)
        output.append("ANSWER:")
        output.append("=" * 80)
        output.append(result['answer'])

        if result['papers']:
            output.append("\n" + "=" * 80)
            output.append("SOURCE PAPERS:")
            output.append("=" * 80)
            for i, paper in enumerate(result['papers'], 1):
                output.append(f"\n[{i}] {paper['title']}")
                if paper['authors']:
                    output.append(f"    Authors: {', '.join(paper['authors'][:3])}")
                output.append(f"    Year: {paper['year']} | Relevance: {paper['relevance_score']:.2f}")

        if result['faculty']:
            output.append("\n" + "=" * 80)
            output.append("RELEVANT FACULTY:")
            output.append("=" * 80)
            for i, member in enumerate(result['faculty'], 1):
                output.append(f"\n[{i}] {member['name']}")
                output.append(f"    {member['title']}, {member['department']}")
                if member['research_areas']:
                    output.append(f"    Research: {', '.join(member['research_areas'][:3])}")

        output.append("\n" + "=" * 80)
        output.append("METRICS:")
        output.append("=" * 80)
        output.append(f"Input tokens: {result['input_tokens']}")
        output.append(f"Output tokens: {result['output_tokens']}")
        output.append(f"Estimated cost: ${result['estimated_cost']:.6f}")

        return "\n".join(output)


def run_demo_queries():
    """Run demonstration queries"""
    print("\n" + "=" * 80)
    print("UCI RESEARCH INTELLIGENCE - RAG SYSTEM DEMO")
    print("=" * 80)

    # Initialize pipeline
    pipeline = RAGPipeline()

    # Demo queries
    demo_queries = [
        "What quantum computing research is happening?",
        "Who works on condensed matter physics?",
        "Summarize recent work on superconductors"
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"\n\n{'=' * 80}")
        print(f"DEMO QUERY {i}: {query}")
        print('=' * 80)

        # Generate answer
        result = pipeline.generate_answer(query)

        # Display formatted response
        print(pipeline.format_response(result))

        input("\n\nPress Enter to continue to next query...")

    # Show total session cost
    print("\n\n" + "=" * 80)
    print("SESSION SUMMARY:")
    print("=" * 80)
    costs = pipeline.get_total_cost()
    print(f"Total input tokens: {costs['total_input_tokens']:,}")
    print(f"Total output tokens: {costs['total_output_tokens']:,}")
    print(f"Total estimated cost: ${costs['total_cost_usd']:.6f}")
    print(f"  - Input cost: ${costs['input_cost_usd']:.6f}")
    print(f"  - Output cost: ${costs['output_cost_usd']:.6f}")


def interactive_mode():
    """Run interactive Q&A mode"""
    print("\n" + "=" * 80)
    print("UCI RESEARCH INTELLIGENCE - INTERACTIVE MODE")
    print("=" * 80)
    print("\nType 'quit' to exit, 'cost' to see running costs")

    pipeline = RAGPipeline()

    while True:
        print("\n" + "-" * 40)
        query = input("Your question: ").strip()

        if query.lower() == 'quit':
            break
        elif query.lower() == 'cost':
            costs = pipeline.get_total_cost()
            print(f"\nSession cost so far: ${costs['total_cost_usd']:.6f}")
            continue
        elif not query:
            continue

        # Generate and display answer
        result = pipeline.generate_answer(query)
        print(pipeline.format_response(result))

    # Final cost summary
    costs = pipeline.get_total_cost()
    print(f"\n\nFinal session cost: ${costs['total_cost_usd']:.6f}")
    print("Thank you for using UCI Research Intelligence!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        run_demo_queries()