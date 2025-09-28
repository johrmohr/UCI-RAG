#!/usr/bin/env python3
"""
RAG System with OpenAI Integration (Alternative to AWS Bedrock)
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag_pipeline.rag_system import RAGPipeline
import json

try:
    import openai
except ImportError:
    print("Installing OpenAI...")
    os.system("pip install openai")
    import openai


class OpenAIRAGPipeline(RAGPipeline):
    """RAG Pipeline using OpenAI instead of AWS Bedrock"""

    # OpenAI pricing (GPT-3.5-turbo)
    GPT35_INPUT_COST = 0.0005   # $0.50 per million tokens
    GPT35_OUTPUT_COST = 0.0015  # $1.50 per million tokens

    def __init__(self, openai_api_key: str = None, **kwargs):
        """Initialize with OpenAI API key"""
        super().__init__(**kwargs)

        # Set OpenAI API key
        if openai_api_key:
            openai.api_key = openai_api_key
        elif os.environ.get("OPENAI_API_KEY"):
            openai.api_key = os.environ["OPENAI_API_KEY"]
        else:
            print("\n⚠️  OpenAI API key not found!")
            print("Set it with: export OPENAI_API_KEY='your-key-here'")
            print("Get a key from: https://platform.openai.com/api-keys")
            self.openai_available = False
            return

        self.openai_available = True
        self.client = openai.OpenAI()
        print("✅ OpenAI initialized successfully")

    def _call_claude_haiku(self, prompt: str):
        """Override to use OpenAI instead"""
        if not self.openai_available:
            return "OpenAI not available. Please set OPENAI_API_KEY environment variable.", 0, 0

        try:
            # Call GPT-3.5-turbo (similar cost to Claude Haiku)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert research assistant analyzing academic papers and faculty at UC Irvine."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )

            answer = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            return answer, input_tokens, output_tokens

        except Exception as e:
            return f"OpenAI error: {str(e)}", 0, 0

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate OpenAI cost"""
        input_cost = (input_tokens / 1000) * self.GPT35_INPUT_COST
        output_cost = (output_tokens / 1000) * self.GPT35_OUTPUT_COST
        return input_cost + output_cost


def test_openai():
    """Test with OpenAI"""
    print("\n" + "=" * 80)
    print("UCI RAG SYSTEM - OpenAI Version")
    print("=" * 80)

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ Please set your OpenAI API key first:")
        print("   export OPENAI_API_KEY='sk-...'")
        print("\nGet a key from: https://platform.openai.com/api-keys")
        return

    pipeline = OpenAIRAGPipeline()

    # Test query
    query = "What quantum computing research is happening at UCI?"
    print(f"\n🔍 Query: {query}\n")

    result = pipeline.generate_answer(query)
    print(pipeline.format_response(result))

    print(f"\n💰 Cost: ${result['estimated_cost']:.4f}")


if __name__ == "__main__":
    test_openai()