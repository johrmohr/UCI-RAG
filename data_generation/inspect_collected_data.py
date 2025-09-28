#!/usr/bin/env python3
"""
Data Inspector for UCI Research Intelligence
============================================
Analyzes and displays statistics about collected ArXiv and NSF data.
Provides quality verification and storage estimates.

Usage: python inspect_collected_data.py [filename]
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Any
import textwrap

# ============================================================================
# TERMINAL COLORS
# ============================================================================

class Colors:
    """Terminal color codes for pretty output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def wrap(cls, text: str, color: str) -> str:
        """Wrap text with color code"""
        return f"{color}{text}{cls.END}"

# Emoji indicators
class Emoji:
    PAPER = "📄"
    PERSON = "👤"
    MONEY = "💰"
    CHART = "📊"
    CHECK = "✅"
    INFO = "ℹ️"
    WARNING = "⚠️"
    FOLDER = "📁"
    ROCKET = "🚀"
    STAR = "⭐"
    CLOCK = "🕒"
    PACKAGE = "📦"

# ============================================================================
# DATA INSPECTOR CLASS
# ============================================================================

class DataInspector:
    """Inspects and analyzes collected research data"""

    def __init__(self, data_file: str = 'uci_research_data.json'):
        """
        Initialize inspector with data file

        Args:
            data_file: Path to JSON data file
        """
        self.data_file = Path(data_file)
        self.data = None
        self.papers = []
        self.faculty = []
        self.grants = []
        self.relationships = {}

    def load_data(self) -> bool:
        """Load JSON data from file"""
        if not self.data_file.exists():
            print(f"{Emoji.WARNING} {Colors.wrap('File not found:', Colors.RED)} {self.data_file}")
            return False

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            self.papers = self.data.get('papers', [])
            self.faculty = self.data.get('faculty', [])
            self.grants = self.data.get('grants', [])
            self.relationships = self.data.get('relationships', {})

            print(f"{Emoji.CHECK} {Colors.wrap('Data loaded successfully!', Colors.GREEN)}")
            return True

        except json.JSONDecodeError as e:
            print(f"{Emoji.WARNING} {Colors.wrap(f'JSON decode error: {e}', Colors.RED)}")
            return False
        except Exception as e:
            print(f"{Emoji.WARNING} {Colors.wrap(f'Error loading data: {e}', Colors.RED)}")
            return False

    def print_header(self, title: str) -> None:
        """Print a formatted section header"""
        print("\n" + "="*70)
        print(Colors.wrap(f"  {title}", Colors.BOLD + Colors.CYAN))
        print("="*70)

    def print_subheader(self, title: str) -> None:
        """Print a formatted subsection header"""
        print(f"\n{Colors.wrap(title, Colors.YELLOW + Colors.BOLD)}")
        print("-"*50)

    def display_overview(self) -> None:
        """Display overall data statistics"""
        self.print_header(f"{Emoji.CHART} DATA OVERVIEW")

        # File information
        file_size = self.data_file.stat().st_size
        print(f"\n{Emoji.FOLDER} {Colors.wrap('File Information:', Colors.BOLD)}")
        print(f"  • File: {self.data_file.name}")
        print(f"  • Size: {self._format_size(file_size)}")

        # Metadata
        metadata = self.data.get('metadata', {})
        if metadata:
            print(f"  • Collection Date: {metadata.get('collection_date', 'Unknown')}")
            print(f"  • Date Range: {metadata.get('date_range', 'Unknown')}")
            print(f"  • Sources: {', '.join(metadata.get('sources', []))}")

        # Document counts
        print(f"\n{Emoji.PACKAGE} {Colors.wrap('Document Counts:', Colors.BOLD)}")
        print(f"  • Papers: {Colors.wrap(str(len(self.papers)), Colors.GREEN)}")
        print(f"  • Faculty: {Colors.wrap(str(len(self.faculty)), Colors.GREEN)}")
        print(f"  • Grants: {Colors.wrap(str(len(self.grants)), Colors.GREEN)}")

        # Relationship counts
        if self.relationships:
            print(f"\n{Emoji.INFO} {Colors.wrap('Relationships:', Colors.BOLD)}")
            paper_authors = self.relationships.get('paper_authors', {})
            grant_faculty = self.relationships.get('grant_faculty', {})
            print(f"  • Papers with linked authors: {len(paper_authors)}")
            print(f"  • Grants with linked faculty: {len(grant_faculty)}")

    def analyze_papers(self) -> None:
        """Analyze paper statistics"""
        if not self.papers:
            print(f"{Emoji.WARNING} No papers found in dataset")
            return

        self.print_header(f"{Emoji.PAPER} PAPER ANALYSIS")

        # Category distribution
        category_counts = defaultdict(int)
        for paper in self.papers:
            for cat in paper.get('categories', []):
                # Get primary category (before the dot)
                primary = cat.split('.')[0]
                category_counts[primary] += 1

        self.print_subheader("Papers by Category")
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_cats[:10]:
            bar = "█" * (count // 2) if count > 1 else "█"
            print(f"  {cat:15} {Colors.wrap(bar, Colors.BLUE)} {count}")

        # Date analysis
        dates = []
        for paper in self.papers:
            try:
                pub_date = paper.get('published', '')
                if pub_date:
                    dates.append(datetime.fromisoformat(pub_date.replace('Z', '+00:00')))
            except:
                pass

        if dates:
            min_date = min(dates)
            max_date = max(dates)
            self.print_subheader("Date Range")
            print(f"  • Earliest paper: {min_date.strftime('%Y-%m-%d')}")
            print(f"  • Latest paper: {max_date.strftime('%Y-%m-%d')}")
            print(f"  • Span: {(max_date - min_date).days} days")

        # Paper length statistics
        abstract_lengths = [len(p.get('abstract', '')) for p in self.papers]
        if abstract_lengths:
            avg_length = sum(abstract_lengths) / len(abstract_lengths)
            self.print_subheader("Abstract Statistics")
            print(f"  • Average length: {avg_length:.0f} characters")
            print(f"  • Shortest: {min(abstract_lengths)} characters")
            print(f"  • Longest: {max(abstract_lengths)} characters")

    def display_top_authors(self) -> None:
        """Display top authors by publication count"""
        if not self.papers:
            return

        self.print_header(f"{Emoji.PERSON} TOP AUTHORS")

        # Count publications per author
        author_counts = Counter()
        author_papers = defaultdict(list)

        for paper in self.papers:
            for author in paper.get('authors', []):
                author_counts[author] += 1
                author_papers[author].append(paper.get('title', 'Untitled'))

        # Display top 10 authors
        self.print_subheader("Most Published Authors (Potential Faculty)")
        top_authors = author_counts.most_common(10)

        for rank, (author, count) in enumerate(top_authors, 1):
            # Check if this author is in faculty list
            is_faculty = any(f['name'] == author for f in self.faculty)
            faculty_marker = f" {Emoji.STAR}" if is_faculty else ""

            print(f"\n  {rank}. {Colors.wrap(author, Colors.BOLD)}{faculty_marker}")
            print(f"     Papers: {Colors.wrap(str(count), Colors.GREEN)}")

            # Show sample paper titles
            sample_papers = author_papers[author][:2]
            for paper_title in sample_papers:
                if len(paper_title) > 60:
                    paper_title = paper_title[:57] + "..."
                print(f"     • {paper_title}")

    def display_sample_papers(self, num_samples: int = 3) -> None:
        """Display sample papers to verify quality"""
        if not self.papers:
            return

        self.print_header(f"{Emoji.PAPER} SAMPLE PAPERS")

        # Select diverse samples
        samples = []
        categories_seen = set()

        for paper in self.papers:
            paper_cats = paper.get('categories', [])
            if paper_cats and paper_cats[0] not in categories_seen:
                samples.append(paper)
                categories_seen.add(paper_cats[0])
                if len(samples) >= num_samples:
                    break

        # If not enough diverse samples, just take first N
        if len(samples) < num_samples:
            samples = self.papers[:num_samples]

        for idx, paper in enumerate(samples, 1):
            print(f"\n{Colors.wrap(f'Sample Paper {idx}:', Colors.YELLOW + Colors.BOLD)}")
            print(f"  {Colors.wrap('Title:', Colors.BOLD)} {paper.get('title', 'N/A')}")
            print(f"  {Colors.wrap('Authors:', Colors.BOLD)} {', '.join(paper.get('authors', [])[:3])}")
            if len(paper.get('authors', [])) > 3:
                print(f"           + {len(paper['authors']) - 3} more")
            print(f"  {Colors.wrap('Categories:', Colors.BOLD)} {', '.join(paper.get('categories', []))}")
            print(f"  {Colors.wrap('ArXiv ID:', Colors.BOLD)} {paper.get('arxiv_id', 'N/A')}")

            # Display abstract (wrapped)
            abstract = paper.get('abstract', 'No abstract available')
            if len(abstract) > 300:
                abstract = abstract[:297] + "..."

            print(f"  {Colors.wrap('Abstract:', Colors.BOLD)}")
            wrapped = textwrap.wrap(abstract, width=65)
            for line in wrapped[:4]:  # Show first 4 lines
                print(f"    {line}")
            if len(wrapped) > 4:
                print(f"    ...")

    def analyze_faculty(self) -> None:
        """Analyze faculty profiles"""
        if not self.faculty:
            print(f"{Emoji.WARNING} No faculty profiles found")
            return

        self.print_header(f"{Emoji.PERSON} FACULTY ANALYSIS")

        # Research area distribution
        research_areas = Counter()
        for fac in self.faculty:
            for area in fac.get('research_areas', []):
                research_areas[area] += 1

        self.print_subheader("Faculty by Research Area")
        for area, count in research_areas.most_common():
            bar = "█" * (count // 2) if count > 1 else "█"
            print(f"  {area:35} {Colors.wrap(bar, Colors.GREEN)} {count}")

        # Title distribution
        titles = Counter(f.get('title', 'Unknown') for f in self.faculty)
        self.print_subheader("Faculty by Title")
        for title, count in titles.most_common():
            print(f"  • {title}: {count}")

        # Publication statistics
        pub_counts = [f.get('publication_count', 0) for f in self.faculty]
        if pub_counts:
            self.print_subheader("Publication Statistics")
            print(f"  • Total faculty: {len(self.faculty)}")
            print(f"  • Average publications: {sum(pub_counts) / len(pub_counts):.1f}")
            print(f"  • Most productive: {max(pub_counts)} papers")
            print(f"  • Least productive: {min(pub_counts)} papers")

    def analyze_grants(self) -> None:
        """Analyze grant data"""
        if not self.grants:
            print(f"\n{Emoji.INFO} No grant data collected")
            return

        self.print_header(f"{Emoji.MONEY} GRANT ANALYSIS")

        # Funding statistics
        amounts = [g.get('amount', 0) for g in self.grants]
        total_funding = sum(amounts)

        self.print_subheader("Funding Statistics")
        print(f"  • Total grants: {len(self.grants)}")
        print(f"  • Total funding: ${total_funding:,.2f}")
        if amounts:
            print(f"  • Average grant: ${sum(amounts) / len(amounts):,.2f}")
            print(f"  • Largest grant: ${max(amounts):,.2f}")
            print(f"  • Smallest grant: ${min(amounts):,.2f}")

        # Institution distribution
        institutions = Counter(g.get('institution', 'Unknown') for g in self.grants)
        self.print_subheader("Top Institutions by Grant Count")
        for inst, count in institutions.most_common(5):
            if len(inst) > 40:
                inst = inst[:37] + "..."
            print(f"  • {inst}: {count} grants")

        # Sample grants
        self.print_subheader("Sample Grants")
        for grant in self.grants[:3]:
            title = grant.get('title', 'N/A')
            if len(title) > 60:
                title = title[:57] + "..."
            amount = grant.get('amount', 0)
            pi = grant.get('pi_name', 'Unknown')
            print(f"\n  • {Colors.wrap(title, Colors.BOLD)}")
            print(f"    PI: {pi}")
            print(f"    Amount: ${amount:,.2f}")

    def estimate_storage(self) -> None:
        """Estimate storage requirements"""
        self.print_header(f"{Emoji.PACKAGE} STORAGE ESTIMATES")

        # Current file size
        file_size = self.data_file.stat().st_size

        print(f"\n{Colors.wrap('Current Data:', Colors.BOLD)}")
        print(f"  • JSON file: {self._format_size(file_size)}")
        print(f"  • Documents: {len(self.papers) + len(self.faculty) + len(self.grants)}")

        # Estimate embeddings storage
        # Assuming 384-dim embeddings (float32 = 4 bytes per dimension)
        embedding_size_per_doc = 384 * 4  # bytes
        total_docs = len(self.papers) + len(self.faculty) + len(self.grants)
        embedding_storage = total_docs * embedding_size_per_doc

        print(f"\n{Colors.wrap('Estimated Embedding Storage:', Colors.BOLD)}")
        print(f"  • Per document: {self._format_size(embedding_size_per_doc)}")
        print(f"  • Total embeddings: {self._format_size(embedding_storage)}")

        # S3 estimates
        total_s3_storage = file_size + embedding_storage
        s3_cost_per_gb = 0.023  # USD per GB per month for S3 Standard
        monthly_cost = (total_s3_storage / (1024**3)) * s3_cost_per_gb

        print(f"\n{Colors.wrap('S3 Storage Estimates:', Colors.BOLD)}")
        print(f"  • Raw data: {self._format_size(file_size)}")
        print(f"  • Embeddings: {self._format_size(embedding_storage)}")
        print(f"  • Total: {self._format_size(total_s3_storage)}")
        print(f"  • Monthly cost: ${monthly_cost:.4f}")

        # ChromaDB estimates (local storage)
        chromadb_overhead = 1.5  # ChromaDB typically has 50% overhead
        chromadb_storage = embedding_storage * chromadb_overhead

        print(f"\n{Colors.wrap('Local ChromaDB Storage:', Colors.BOLD)}")
        print(f"  • Estimated size: {self._format_size(chromadb_storage)}")
        print(f"  • Location: data/chroma/")

    def _format_size(self, bytes_size: int) -> str:
        """Format byte size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"

    def generate_report(self) -> None:
        """Generate complete inspection report"""
        print("\n" + "="*70)
        print(Colors.wrap(f"{Emoji.ROCKET} UCI RESEARCH INTELLIGENCE - DATA INSPECTION REPORT",
                         Colors.BOLD + Colors.HEADER))
        print("="*70)

        self.display_overview()
        self.analyze_papers()
        self.display_top_authors()
        self.display_sample_papers()
        self.analyze_faculty()
        self.analyze_grants()
        self.estimate_storage()

        # Final summary
        self.print_header(f"{Emoji.CHECK} DATA QUALITY SUMMARY")

        quality_checks = []

        # Check papers
        if len(self.papers) >= 100:
            quality_checks.append((True, f"Sufficient papers ({len(self.papers)})"))
        else:
            quality_checks.append((False, f"Low paper count ({len(self.papers)})"))

        # Check abstracts
        if self.papers:
            avg_abstract_len = sum(len(p.get('abstract', '')) for p in self.papers) / len(self.papers)
            if avg_abstract_len > 500:
                quality_checks.append((True, f"Good abstract length (avg {avg_abstract_len:.0f} chars)"))
            else:
                quality_checks.append((False, f"Short abstracts (avg {avg_abstract_len:.0f} chars)"))

        # Check faculty
        if len(self.faculty) >= 20:
            quality_checks.append((True, f"Good faculty count ({len(self.faculty)})"))
        else:
            quality_checks.append((False, f"Low faculty count ({len(self.faculty)})"))

        # Check relationships
        if self.relationships and len(self.relationships.get('paper_authors', {})) > 0:
            quality_checks.append((True, "Paper-author relationships present"))
        else:
            quality_checks.append((False, "No paper-author relationships"))

        # Display checks
        print()
        for passed, message in quality_checks:
            icon = Emoji.CHECK if passed else Emoji.WARNING
            color = Colors.GREEN if passed else Colors.YELLOW
            print(f"  {icon} {Colors.wrap(message, color)}")

        # Overall assessment
        passed_count = sum(1 for p, _ in quality_checks if p)
        total_checks = len(quality_checks)

        print(f"\n  {Colors.wrap('Overall Quality:', Colors.BOLD)} ", end="")
        if passed_count == total_checks:
            print(Colors.wrap("EXCELLENT", Colors.GREEN + Colors.BOLD))
        elif passed_count >= total_checks * 0.75:
            print(Colors.wrap("GOOD", Colors.GREEN))
        elif passed_count >= total_checks * 0.5:
            print(Colors.wrap("ACCEPTABLE", Colors.YELLOW))
        else:
            print(Colors.wrap("NEEDS IMPROVEMENT", Colors.RED))

        print(f"\n{Colors.wrap('Ready for:', Colors.BOLD)}")
        print(f"  ✓ Embedding generation")
        print(f"  ✓ Vector database indexing")
        print(f"  ✓ RAG pipeline testing")
        print(f"  ✓ Demo presentations")

        print("\n" + "="*70)
        print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""

    # Check command line arguments
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        # Look for default file
        default_files = [
            'uci_research_data.json',
            'data_generation/uci_research_data.json',
            '../data_generation/uci_research_data.json'
        ]

        data_file = None
        for file in default_files:
            if Path(file).exists():
                data_file = file
                break

        if not data_file:
            print(f"{Emoji.WARNING} No data file specified and default not found.")
            print(f"Usage: python {sys.argv[0]} [data_file.json]")
            print(f"\nLooking for one of:")
            for file in default_files:
                print(f"  • {file}")
            sys.exit(1)

    # Create inspector and run analysis
    inspector = DataInspector(data_file)

    if inspector.load_data():
        inspector.generate_report()
    else:
        print(f"\n{Emoji.WARNING} Failed to load data. Please check the file path.")
        sys.exit(1)

if __name__ == "__main__":
    main()