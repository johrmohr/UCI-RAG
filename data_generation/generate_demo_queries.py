#!/usr/bin/env python3
"""
Generate demo queries based on actual collected ArXiv data.
Creates queries that will return meaningful results from the real dataset.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import random
import re

class DemoQueryGenerator:
    def __init__(self):
        """Initialize the query generator."""
        self.data_file = Path("data_generation/uci_research_data.json")
        self.output_file = Path("data_generation/demo_queries.json")
        self.data = None
        self.stats = {}

    def load_data(self) -> bool:
        """Load the collected research data."""
        if not self.data_file.exists():
            print(f"❌ Data file not found: {self.data_file}")
            return False

        print(f"📚 Loading data from {self.data_file}")
        with open(self.data_file, 'r') as f:
            self.data = json.load(f)

        print(f"✅ Loaded {len(self.data.get('papers', []))} papers")
        print(f"✅ Loaded {len(self.data.get('faculty', []))} faculty members")
        return True

    def analyze_data(self):
        """Analyze the data to find patterns for query generation."""
        print("\n📊 Analyzing data for query generation...")

        papers = self.data.get('papers', [])
        faculty = self.data.get('faculty', [])

        # Analyze authors
        author_counts = Counter()
        author_topics = defaultdict(set)
        for paper in papers:
            for author in paper.get('authors', []):
                author_name = author if isinstance(author, str) else author.get('name', '')
                author_counts[author_name] += 1

                # Track topics for this author
                categories = paper.get('categories', [])
                for cat in categories:
                    author_topics[author_name].add(cat)

        # Find prolific authors (more than 2 papers)
        prolific_authors = [(author, count) for author, count in author_counts.most_common(20)
                           if count >= 2]

        # Analyze topics/categories
        category_counts = Counter()
        category_keywords = defaultdict(set)
        for paper in papers:
            for cat in paper.get('categories', []):
                category_counts[cat] += 1

                # Extract keywords from title and summary
                title = paper.get('title', '').lower()
                summary = paper.get('summary', '')[:500].lower()

                # Extract meaningful keywords
                keywords = self._extract_keywords(title + ' ' + summary)
                for keyword in keywords:
                    category_keywords[cat].add(keyword)

        # Analyze time trends
        recent_papers = []
        for paper in papers:
            pub_date = paper.get('published', '')
            if pub_date and pub_date.startswith('202'):  # Recent papers
                year = int(pub_date[:4])
                if year >= 2023:
                    recent_papers.append(paper)

        # Extract trending topics from recent papers
        trending_topics = Counter()
        for paper in recent_papers[-50:]:  # Last 50 papers
            keywords = self._extract_keywords(paper.get('title', '') + ' ' + paper.get('summary', '')[:200])
            for keyword in keywords:
                trending_topics[keyword] += 1

        # Find papers with specific characteristics
        quantum_papers = [p for p in papers if 'quantum' in p.get('title', '').lower() or 'quantum' in p.get('summary', '').lower()[:500]]
        ml_papers = [p for p in papers if any(term in p.get('title', '').lower() or term in p.get('summary', '').lower()[:500]
                                              for term in ['machine learning', 'neural', 'deep learning', 'artificial intelligence'])]
        astro_papers = [p for p in papers if any(term in p.get('title', '').lower() or term in p.get('summary', '').lower()[:500]
                                                 for term in ['cosmic', 'galaxy', 'stellar', 'astrophysics', 'cosmology'])]

        # Store analysis results
        self.stats = {
            'prolific_authors': prolific_authors[:10],
            'author_topics': {author: list(topics)[:5] for author, topics in author_topics.items() if author_counts[author] >= 2},
            'top_categories': category_counts.most_common(10),
            'category_keywords': {cat: list(keywords)[:10] for cat, keywords in category_keywords.items()},
            'trending_topics': trending_topics.most_common(15),
            'recent_paper_count': len(recent_papers),
            'quantum_paper_count': len(quantum_papers),
            'ml_paper_count': len(ml_papers),
            'astro_paper_count': len(astro_papers),
            'sample_quantum_papers': quantum_papers[:3] if quantum_papers else [],
            'sample_ml_papers': ml_papers[:3] if ml_papers else [],
            'sample_astro_papers': astro_papers[:3] if astro_papers else [],
            'faculty_names': [f.get('name', '') for f in faculty if f.get('name')]
        }

        print(f"  • Found {len(prolific_authors)} prolific authors")
        print(f"  • Identified {len(self.stats['top_categories'])} main categories")
        print(f"  • Found {len(trending_topics)} trending topics")
        print(f"  • {len(quantum_papers)} quantum physics papers")
        print(f"  • {len(ml_papers)} ML/AI papers")
        print(f"  • {len(astro_papers)} astrophysics papers")

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Important physics and CS terms to look for
        important_terms = [
            'quantum', 'entanglement', 'superconducting', 'topological', 'photonic',
            'neural', 'transformer', 'diffusion', 'optimization', 'bayesian',
            'cosmology', 'dark matter', 'black hole', 'gravitational', 'galaxy',
            'particle', 'hadron', 'quark', 'boson', 'fermion',
            'condensed matter', 'phase transition', 'magnetism', 'semiconductor',
            'laser', 'optics', 'spectroscopy', 'interferometry',
            'field theory', 'symmetry', 'renormalization', 'string theory'
        ]

        keywords = []
        text_lower = text.lower()

        for term in important_terms:
            if term in text_lower:
                keywords.append(term)

        # Also extract capitalized words that might be techniques or names
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        for word in words[:10]:  # Limit to avoid too many
            if len(word) > 4 and word.lower() not in ['this', 'these', 'that', 'with', 'from']:
                keywords.append(word.lower())

        return list(set(keywords))[:15]  # Return unique keywords, max 15

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate demo queries based on the analysis."""
        print("\n🎯 Generating demo queries...")

        queries = []

        # 1. Simple lookup queries (EASY)
        if self.stats['prolific_authors']:
            # Query for prolific author
            author, count = self.stats['prolific_authors'][0]
            queries.append({
                'query': f'Show me papers by {author}',
                'category': 'simple_lookup',
                'difficulty': 'easy',
                'expected_results': f'Should return approximately {count} papers',
                'type': 'author_search'
            })

            # Query for author with specific topic
            if len(self.stats['prolific_authors']) > 1:
                author2, _ = self.stats['prolific_authors'][1]
                if author2 in self.stats['author_topics']:
                    topics = self.stats['author_topics'][author2]
                    if topics:
                        queries.append({
                            'query': f'What has {author2} published on {topics[0]}?',
                            'category': 'filtered_search',
                            'difficulty': 'medium',
                            'expected_results': f'Papers by {author2} in category {topics[0]}',
                            'type': 'author_topic_search'
                        })

        # 2. Topic-based queries (EASY-MEDIUM)
        if self.stats['top_categories']:
            for cat, count in self.stats['top_categories'][:3]:
                # Simple category query
                queries.append({
                    'query': f'Find recent papers in {cat}',
                    'category': 'simple_lookup',
                    'difficulty': 'easy',
                    'expected_results': f'Should return papers from {cat} category ({count} total available)',
                    'type': 'category_search'
                })

                # Category with keywords
                if cat in self.stats['category_keywords'] and self.stats['category_keywords'][cat]:
                    keyword = self.stats['category_keywords'][cat][0]
                    queries.append({
                        'query': f'Show me {cat} papers about {keyword}',
                        'category': 'filtered_search',
                        'difficulty': 'medium',
                        'expected_results': f'Papers in {cat} mentioning {keyword}',
                        'type': 'category_keyword_search'
                    })

        # 3. Trending topic queries (MEDIUM)
        if self.stats['trending_topics']:
            for topic, count in self.stats['trending_topics'][:3]:
                queries.append({
                    'query': f'What are the latest advances in {topic}?',
                    'category': 'trend_analysis',
                    'difficulty': 'medium',
                    'expected_results': f'Recent papers mentioning {topic} (found in {count} recent papers)',
                    'type': 'trending_search'
                })

        # 4. Specific domain queries based on actual data
        if self.stats['quantum_paper_count'] > 0:
            queries.append({
                'query': 'Show me recent work on quantum computing and quantum information',
                'category': 'domain_specific',
                'difficulty': 'easy',
                'expected_results': f'Should return quantum-related papers ({self.stats["quantum_paper_count"]} available)',
                'type': 'quantum_search'
            })

            if self.stats['sample_quantum_papers']:
                sample_title = self.stats['sample_quantum_papers'][0].get('title', '')
                sample_keywords = self._extract_keywords(sample_title)
                if sample_keywords:
                    queries.append({
                        'query': f'Find papers about {sample_keywords[0]} in quantum physics',
                        'category': 'domain_specific',
                        'difficulty': 'medium',
                        'expected_results': f'Papers combining {sample_keywords[0]} and quantum concepts',
                        'type': 'quantum_specific_search'
                    })

        if self.stats['ml_paper_count'] > 0:
            queries.append({
                'query': 'What machine learning techniques are being applied in physics research?',
                'category': 'interdisciplinary',
                'difficulty': 'hard',
                'expected_results': f'Papers at intersection of ML and physics ({self.stats["ml_paper_count"]} ML papers found)',
                'type': 'ml_physics_search'
            })

        if self.stats['astro_paper_count'] > 0:
            queries.append({
                'query': 'Show me recent astrophysics and cosmology papers',
                'category': 'domain_specific',
                'difficulty': 'easy',
                'expected_results': f'Astrophysics papers ({self.stats["astro_paper_count"]} available)',
                'type': 'astro_search'
            })

        # 5. Complex reasoning queries (HARD)
        queries.append({
            'query': 'Who are the most active researchers in quantum physics this year?',
            'category': 'analytical',
            'difficulty': 'hard',
            'expected_results': 'Authors with multiple quantum papers in 2023-2024',
            'type': 'active_researcher_analysis'
        })

        queries.append({
            'query': 'What are the emerging research areas combining physics and computer science?',
            'category': 'analytical',
            'difficulty': 'hard',
            'expected_results': 'Papers showing CS-physics intersection, especially ML applications',
            'type': 'interdisciplinary_analysis'
        })

        # 6. Faculty-specific queries if we have faculty data
        if self.stats['faculty_names']:
            for faculty_name in self.stats['faculty_names'][:2]:
                queries.append({
                    'query': f'What is {faculty_name} working on?',
                    'category': 'faculty_search',
                    'difficulty': 'easy',
                    'expected_results': f'Information about {faculty_name} and their research',
                    'type': 'faculty_lookup'
                })

        # 7. Time-based queries
        queries.append({
            'query': 'Show me papers published in the last month',
            'category': 'temporal',
            'difficulty': 'easy',
            'expected_results': f'Most recent papers (found {self.stats["recent_paper_count"]} papers from 2023+)',
            'type': 'recent_papers'
        })

        queries.append({
            'query': 'What were the breakthrough papers in 2024?',
            'category': 'temporal',
            'difficulty': 'hard',
            'expected_results': 'Significant papers from 2024, possibly with high impact',
            'type': 'breakthrough_analysis'
        })

        # 8. Collaboration queries
        queries.append({
            'query': 'Find papers with international collaborations',
            'category': 'analytical',
            'difficulty': 'hard',
            'expected_results': 'Papers with authors from multiple institutions/countries',
            'type': 'collaboration_analysis'
        })

        # 9. Method-specific queries
        queries.append({
            'query': 'Which papers use deep learning for physics problems?',
            'category': 'methodology',
            'difficulty': 'medium',
            'expected_results': 'Papers mentioning neural networks, deep learning in physics context',
            'type': 'method_search'
        })

        queries.append({
            'query': 'Show me experimental physics papers versus theoretical ones',
            'category': 'analytical',
            'difficulty': 'hard',
            'expected_results': 'Classification of papers by experimental vs theoretical approach',
            'type': 'approach_classification'
        })

        # 10. Specific technical queries based on real data
        technical_terms = ['entanglement', 'superconductor', 'dark matter', 'neural network', 'topology']
        for term in technical_terms:
            # Check if this term actually appears in our data
            term_papers = [p for p in self.data.get('papers', [])
                          if term in p.get('title', '').lower() or term in p.get('summary', '').lower()[:500]]
            if len(term_papers) >= 2:
                queries.append({
                    'query': f'Explain the latest research on {term}',
                    'category': 'explanation',
                    'difficulty': 'medium',
                    'expected_results': f'Summary of {term} research ({len(term_papers)} papers found)',
                    'type': 'technical_explanation'
                })
                break

        print(f"✅ Generated {len(queries)} demo queries")
        return queries

    def save_queries(self, queries: List[Dict[str, Any]]):
        """Save queries to JSON file with statistics."""
        print(f"\n💾 Saving queries to {self.output_file}")

        # Organize queries by category and difficulty
        by_category = defaultdict(list)
        by_difficulty = defaultdict(list)

        for query in queries:
            by_category[query['category']].append(query)
            by_difficulty[query['difficulty']].append(query)

        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_source': str(self.data_file),
                'total_queries': len(queries),
                'papers_analyzed': len(self.data.get('papers', [])),
                'faculty_analyzed': len(self.data.get('faculty', [])),
            },
            'statistics': {
                'by_category': {cat: len(qs) for cat, qs in by_category.items()},
                'by_difficulty': {diff: len(qs) for diff, qs in by_difficulty.items()},
                'data_insights': {
                    'prolific_authors': self.stats.get('prolific_authors', [])[:5],
                    'top_categories': self.stats.get('top_categories', [])[:5],
                    'trending_topics': self.stats.get('trending_topics', [])[:10]
                }
            },
            'queries': queries,
            'usage_notes': {
                'easy': 'Simple keyword or author lookups that should return direct matches',
                'medium': 'Queries requiring some filtering or combination of criteria',
                'hard': 'Complex analytical queries requiring reasoning across multiple papers'
            }
        }

        with open(self.output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"✅ Saved {len(queries)} queries")
        print(f"\n📊 Query Distribution:")
        print(f"  By difficulty:")
        for diff, count in output['statistics']['by_difficulty'].items():
            print(f"    • {diff}: {count}")
        print(f"  By category:")
        for cat, count in output['statistics']['by_category'].items():
            print(f"    • {cat}: {count}")

    def display_sample_queries(self, queries: List[Dict[str, Any]]):
        """Display a sample of generated queries."""
        print("\n📝 Sample Generated Queries:")
        print("="*60)

        # Show 2 from each difficulty level
        for difficulty in ['easy', 'medium', 'hard']:
            difficulty_queries = [q for q in queries if q['difficulty'] == difficulty]
            print(f"\n{difficulty.upper()} Queries:")
            for query in difficulty_queries[:2]:
                print(f"  Q: {query['query']}")
                print(f"     → Expected: {query['expected_results']}")
                print()

    def run(self):
        """Main execution method."""
        print("\n" + "="*60)
        print("🎯 Demo Query Generator")
        print("="*60)

        # Load data
        if not self.load_data():
            return

        # Analyze data
        self.analyze_data()

        # Generate queries
        queries = self.generate_queries()

        # Save queries
        self.save_queries(queries)

        # Display samples
        self.display_sample_queries(queries)

        print("\n✨ Query generation complete!")
        print(f"📄 Queries saved to: {self.output_file}")
        print("\n💡 These queries are designed to work with your actual dataset")
        print("   and will return meaningful results when used with the RAG system.")

if __name__ == "__main__":
    generator = DemoQueryGenerator()
    generator.run()