#!/usr/bin/env python3
"""
ArXiv and NSF Data Collection Script for UCI Research Intelligence
===================================================================
Collects real physics research papers from ArXiv and grant data from NSF API.
Creates a realistic dataset for the RAG pipeline demonstration.

Usage: python collect_arxiv_data.py
"""

import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import re
import sys
from pathlib import Path
import urllib.parse
import xml.etree.ElementTree as ET

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.config import uci_physics_config

# ============================================================================
# CONFIGURATION
# ============================================================================

# ArXiv categories to collect
ARXIV_CATEGORIES = [
    'quant-ph',      # Quantum Physics
    'hep-th',        # High Energy Physics - Theory
    'cond-mat',      # Condensed Matter
    'gr-qc',         # General Relativity and Quantum Cosmology
    'physics.bio-ph', # Biological Physics
    'astro-ph',      # Astrophysics (all subcategories)
]

# Collection parameters
PAPERS_PER_CATEGORY = 35  # ~200 total papers
TOTAL_PAPERS_TARGET = 200
START_DATE = '2022-01-01'
END_DATE = '2024-12-31'

# NSF Award API parameters
NSF_API_BASE = 'https://api.nsf.gov/services/v1/awards.json'
NSF_KEYWORDS = ['physics', 'quantum', 'photonics', 'materials', 'astrophysics', 'particle']
NSF_STATE = 'CA'  # California
GRANTS_TARGET = 50

# Rate limiting
ARXIV_DELAY = 3  # seconds between ArXiv API calls
NSF_DELAY = 1    # seconds between NSF API calls

# Output file
OUTPUT_FILE = 'uci_research_data.json'

# ============================================================================
# ARXIV DATA COLLECTION
# ============================================================================

class ArXivCollector:
    """Collects research papers from ArXiv API"""

    def __init__(self):
        self.base_url = 'http://export.arxiv.org/api/query'
        self.papers = []
        self.authors_count = defaultdict(int)
        self.author_papers = defaultdict(list)

    def collect_papers(self, categories: List[str], max_results: int = 200) -> List[Dict]:
        """
        Collect papers from specified ArXiv categories

        Args:
            categories: List of ArXiv category codes
            max_results: Maximum number of papers to collect

        Returns:
            List of paper dictionaries
        """
        print("\n" + "="*60)
        print("COLLECTING ARXIV PAPERS")
        print("="*60)

        all_papers = []
        papers_per_cat = max_results // len(categories)

        for category in categories:
            print(f"\n📚 Collecting papers from {category}...")
            papers = self._query_arxiv(category, papers_per_cat)
            all_papers.extend(papers)
            print(f"   ✓ Collected {len(papers)} papers from {category}")
            time.sleep(ARXIV_DELAY)

        # Process authors
        self._process_authors(all_papers)

        print(f"\n✅ Total papers collected: {len(all_papers)}")
        return all_papers

    def _query_arxiv(self, category: str, max_results: int) -> List[Dict]:
        """Query ArXiv API for papers in a category"""

        # Build query for recent papers (2022-2024)
        query = f'cat:{category}'

        params = {
            'search_query': query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.text)

            # Extract papers
            papers = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                paper = self._parse_entry(entry, category)

                # Filter by date
                pub_date = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
                if pub_date.year >= 2022:
                    papers.append(paper)

                    # Track authors
                    for author in paper['authors']:
                        self.authors_count[author] += 1
                        self.author_papers[author].append(paper['arxiv_id'])

            return papers[:max_results]

        except Exception as e:
            print(f"   ⚠️  Error querying ArXiv: {e}")
            return []

    def _parse_entry(self, entry, primary_category: str) -> Dict:
        """Parse ArXiv entry XML into paper dictionary"""

        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}

        # Extract basic fields
        paper = {
            'arxiv_id': entry.find('atom:id', ns).text.split('/')[-1],
            'title': ' '.join(entry.find('atom:title', ns).text.split()),
            'abstract': ' '.join(entry.find('atom:summary', ns).text.split()),
            'published': entry.find('atom:published', ns).text,
            'updated': entry.find('atom:updated', ns).text,
        }

        # Extract authors
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns).text
            authors.append(name)
        paper['authors'] = authors

        # Extract categories
        categories = [primary_category]
        for category in entry.findall('atom:category', ns):
            cat = category.get('term')
            if cat and cat != primary_category:
                categories.append(cat)
        paper['categories'] = categories

        # Extract comment (often mentions journal acceptance)
        comment = entry.find('arxiv:comment', ns)
        paper['comment'] = comment.text if comment is not None else None

        # Extract links
        paper['pdf_link'] = f"https://arxiv.org/pdf/{paper['arxiv_id']}.pdf"
        paper['abs_link'] = f"https://arxiv.org/abs/{paper['arxiv_id']}"

        # Add metadata
        paper['source'] = 'arxiv'
        paper['document_type'] = 'research_paper'

        return paper

    def _process_authors(self, papers: List[Dict]) -> None:
        """Process authors to identify frequent publishers"""

        # Find authors with 3+ papers
        self.frequent_authors = {
            author: count
            for author, count in self.authors_count.items()
            if count >= 3
        }

        print(f"\n👥 Found {len(self.frequent_authors)} authors with 3+ papers")

# ============================================================================
# NSF GRANT DATA COLLECTION
# ============================================================================

class NSFCollector:
    """Collects grant data from NSF API"""

    def __init__(self):
        self.base_url = NSF_API_BASE
        self.grants = []

    def collect_grants(self, keywords: List[str], state: str = 'CA',
                       max_results: int = 50) -> List[Dict]:
        """
        Collect NSF grants related to physics in California

        Args:
            keywords: Keywords to search for
            state: State code
            max_results: Maximum grants to collect

        Returns:
            List of grant dictionaries
        """
        print("\n" + "="*60)
        print("COLLECTING NSF GRANTS")
        print("="*60)

        all_grants = []
        grants_per_keyword = max_results // len(keywords)

        for keyword in keywords:
            print(f"\n💰 Searching NSF grants for '{keyword}'...")
            grants = self._query_nsf(keyword, state, grants_per_keyword)
            all_grants.extend(grants)
            print(f"   ✓ Found {len(grants)} grants")
            time.sleep(NSF_DELAY)

        # Remove duplicates based on award ID
        unique_grants = {}
        for grant in all_grants:
            unique_grants[grant['award_id']] = grant

        final_grants = list(unique_grants.values())[:max_results]
        print(f"\n✅ Total unique grants collected: {len(final_grants)}")

        return final_grants

    def _query_nsf(self, keyword: str, state: str, limit: int = 25) -> List[Dict]:
        """Query NSF API for grants"""

        params = {
            'keyword': keyword,
            'awardeeName': state,  # Filter by state
            'offset': 0,
            'printFields': 'id,title,awardeeName,piFirstName,piLastName,date,expDate,awardeeName,fundsObligatedAmt,abstractText',
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()

            grants = []
            if 'response' in data and 'award' in data['response']:
                for award in data['response']['award'][:limit]:
                    grant = self._parse_award(award)
                    if grant and self._is_physics_related(grant):
                        grants.append(grant)

            return grants

        except Exception as e:
            print(f"   ⚠️  Error querying NSF: {e}")
            return []

    def _parse_award(self, award: Dict) -> Optional[Dict]:
        """Parse NSF award into grant dictionary"""

        try:
            # Extract grant information
            grant = {
                'award_id': award.get('id', ''),
                'title': award.get('title', ''),
                'pi_name': f"{award.get('piFirstName', '')} {award.get('piLastName', '')}".strip(),
                'institution': award.get('awardeeName', ''),
                'amount': float(award.get('fundsObligatedAmt', 0)),
                'start_date': award.get('date', ''),
                'end_date': award.get('expDate', ''),
                'abstract': award.get('abstractText', ''),
                'source': 'nsf',
                'document_type': 'grant'
            }

            # Only return if has essential fields
            if grant['award_id'] and grant['title']:
                return grant
            return None

        except Exception as e:
            print(f"   ⚠️  Error parsing award: {e}")
            return None

    def _is_physics_related(self, grant: Dict) -> bool:
        """Check if grant is physics-related"""

        text = f"{grant['title']} {grant['abstract']}".lower()

        physics_terms = [
            'physics', 'quantum', 'particle', 'cosmology', 'astrophysics',
            'condensed matter', 'photonics', 'laser', 'optics', 'materials',
            'nanoscale', 'semiconductor', 'superconductor', 'magnetism'
        ]

        return any(term in text for term in physics_terms)

# ============================================================================
# FACULTY PROFILE GENERATION
# ============================================================================

class FacultyGenerator:
    """Generates faculty profiles from frequent authors"""

    # UCI Physics research areas for assignment
    RESEARCH_AREAS = [
        "Quantum Information Science",
        "Condensed Matter Physics",
        "High Energy Physics",
        "Astrophysics and Cosmology",
        "Atomic, Molecular, and Optical Physics",
        "Biological Physics",
        "Theoretical Physics",
        "Experimental Particle Physics"
    ]

    # Academic titles
    TITLES = [
        "Professor",
        "Associate Professor",
        "Assistant Professor",
        "Distinguished Professor",
        "Research Professor"
    ]

    def __init__(self):
        self.faculty_profiles = []

    def generate_profiles(self, frequent_authors: Dict[str, int],
                         author_papers: Dict[str, List[str]],
                         papers: List[Dict]) -> List[Dict]:
        """
        Generate faculty profiles from frequent authors

        Args:
            frequent_authors: Authors with publication counts
            author_papers: Mapping of authors to their paper IDs
            papers: List of all papers

        Returns:
            List of faculty profile dictionaries
        """
        print("\n" + "="*60)
        print("GENERATING FACULTY PROFILES")
        print("="*60)

        # Sort authors by publication count
        sorted_authors = sorted(frequent_authors.items(),
                              key=lambda x: x[1], reverse=True)

        # Take top 50 as "UCI faculty" for demo
        top_authors = sorted_authors[:50]

        for idx, (author_name, pub_count) in enumerate(top_authors):
            profile = self._create_profile(
                author_name,
                pub_count,
                author_papers[author_name],
                papers,
                idx
            )
            self.faculty_profiles.append(profile)

        print(f"\n✅ Generated {len(self.faculty_profiles)} faculty profiles")
        return self.faculty_profiles

    def _create_profile(self, name: str, pub_count: int,
                       paper_ids: List[str], all_papers: List[Dict],
                       idx: int) -> Dict:
        """Create a single faculty profile"""

        # Get author's papers
        author_papers = [p for p in all_papers if p['arxiv_id'] in paper_ids]

        # Determine research area based on paper categories
        research_area = self._determine_research_area(author_papers)

        # Assign title based on publication count
        if pub_count >= 10:
            title = "Distinguished Professor"
        elif pub_count >= 7:
            title = "Professor"
        elif pub_count >= 5:
            title = "Associate Professor"
        else:
            title = "Assistant Professor"

        # Create profile
        profile = {
            'faculty_id': f"UCI_PHYS_{idx+1:03d}",
            'name': name,
            'title': title,
            'department': "Physics and Astronomy",
            'university': "University of California, Irvine",
            'email': f"{name.lower().replace(' ', '.').replace(',', '')}@uci.edu",
            'research_areas': [research_area],
            'publication_count': pub_count,
            'recent_papers': paper_ids[:5],  # Last 5 papers
            'keywords': self._extract_keywords(author_papers),
            'h_index': min(pub_count * 2, 50),  # Simulated h-index
            'citations': pub_count * 150,  # Simulated citations
            'document_type': 'faculty_profile'
        }

        return profile

    def _determine_research_area(self, papers: List[Dict]) -> str:
        """Determine research area from paper categories"""

        category_mapping = {
            'quant-ph': "Quantum Information Science",
            'cond-mat': "Condensed Matter Physics",
            'hep-th': "High Energy Physics",
            'hep-ph': "High Energy Physics",
            'hep-ex': "Experimental Particle Physics",
            'astro-ph': "Astrophysics and Cosmology",
            'gr-qc': "Astrophysics and Cosmology",
            'physics.bio-ph': "Biological Physics",
            'physics.atom-ph': "Atomic, Molecular, and Optical Physics",
            'physics.optics': "Atomic, Molecular, and Optical Physics"
        }

        # Count categories
        category_counts = defaultdict(int)
        for paper in papers:
            for cat in paper.get('categories', []):
                base_cat = cat.split('.')[0]
                if base_cat in category_mapping:
                    category_counts[category_mapping[base_cat]] += 1
                elif cat in category_mapping:
                    category_counts[category_mapping[cat]] += 1

        # Return most common area
        if category_counts:
            return max(category_counts.items(), key=lambda x: x[1])[0]
        return "Theoretical Physics"

    def _extract_keywords(self, papers: List[Dict], max_keywords: int = 10) -> List[str]:
        """Extract keywords from paper titles and abstracts"""

        # Common physics terms to look for
        physics_terms = [
            'quantum', 'entanglement', 'superconductor', 'semiconductor',
            'nanoparticle', 'graphene', 'topological', 'fermion', 'boson',
            'symmetry', 'phase transition', 'spin', 'magnetic', 'optical',
            'laser', 'photonic', 'cosmology', 'dark matter', 'neutrino',
            'quark', 'hadron', 'gauge', 'field theory', 'lattice'
        ]

        # Count term occurrences
        term_counts = defaultdict(int)

        for paper in papers:
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
            for term in physics_terms:
                if term in text:
                    term_counts[term] += 1

        # Return top keywords
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in sorted_terms[:max_keywords]]

# ============================================================================
# DATA RELATIONSHIPS
# ============================================================================

def create_relationships(papers: List[Dict], faculty: List[Dict],
                        grants: List[Dict]) -> Dict:
    """
    Create relationships between papers, faculty, and grants

    Returns:
        Dictionary with relationship mappings
    """
    print("\n" + "="*60)
    print("CREATING DATA RELATIONSHIPS")
    print("="*60)

    relationships = {
        'paper_authors': defaultdict(list),  # paper_id -> [faculty_ids]
        'author_papers': defaultdict(list),  # faculty_id -> [paper_ids]
        'grant_faculty': defaultdict(list),  # grant_id -> [faculty_ids]
        'faculty_grants': defaultdict(list),  # faculty_id -> [grant_ids]
    }

    # Create faculty name to ID mapping
    faculty_by_name = {f['name']: f['faculty_id'] for f in faculty}

    # Link papers to faculty
    for paper in papers:
        paper_id = paper['arxiv_id']
        for author in paper['authors']:
            if author in faculty_by_name:
                faculty_id = faculty_by_name[author]
                relationships['paper_authors'][paper_id].append(faculty_id)
                relationships['author_papers'][faculty_id].append(paper_id)

    # Randomly assign some grants to faculty (for demo purposes)
    import random
    for grant in grants[:30]:  # Assign first 30 grants
        grant_id = grant['award_id']
        # Pick 1-3 random faculty as investigators
        selected_faculty = random.sample(faculty, min(3, len(faculty)))
        for fac in selected_faculty:
            relationships['grant_faculty'][grant_id].append(fac['faculty_id'])
            relationships['faculty_grants'][fac['faculty_id']].append(grant_id)

    print(f"✅ Created relationships:")
    print(f"   • Paper-Author links: {len(relationships['paper_authors'])}")
    print(f"   • Grant-Faculty links: {len(relationships['grant_faculty'])}")

    return dict(relationships)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main data collection workflow"""

    print("\n" + "🚀 UCI RESEARCH INTELLIGENCE - DATA COLLECTION")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Collect ArXiv papers
    arxiv_collector = ArXivCollector()
    papers = arxiv_collector.collect_papers(ARXIV_CATEGORIES, TOTAL_PAPERS_TARGET)

    # Generate faculty profiles
    faculty_gen = FacultyGenerator()
    faculty = faculty_gen.generate_profiles(
        arxiv_collector.frequent_authors,
        arxiv_collector.author_papers,
        papers
    )

    # Collect NSF grants
    nsf_collector = NSFCollector()
    grants = nsf_collector.collect_grants(NSF_KEYWORDS, NSF_STATE, GRANTS_TARGET)

    # Create relationships
    relationships = create_relationships(papers, faculty, grants)

    # Prepare final dataset
    dataset = {
        'metadata': {
            'collection_date': datetime.now().isoformat(),
            'sources': ['ArXiv API', 'NSF Award API'],
            'paper_count': len(papers),
            'faculty_count': len(faculty),
            'grant_count': len(grants),
            'categories': ARXIV_CATEGORIES,
            'date_range': f"{START_DATE} to {END_DATE}"
        },
        'papers': papers,
        'faculty': faculty,
        'grants': grants,
        'relationships': relationships
    }

    # Save to file
    output_path = Path(__file__).parent / OUTPUT_FILE
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("✅ DATA COLLECTION COMPLETE")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   • Papers collected: {len(papers)}")
    print(f"   • Faculty profiles: {len(faculty)}")
    print(f"   • Grants collected: {len(grants)}")
    print(f"   • Output saved to: {output_path}")
    print(f"   • File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    # Print sample data
    print(f"\n📄 Sample Paper:")
    if papers:
        sample = papers[0]
        print(f"   Title: {sample['title'][:80]}...")
        print(f"   Authors: {', '.join(sample['authors'][:3])}")
        print(f"   Categories: {', '.join(sample['categories'])}")

    print(f"\n👤 Sample Faculty:")
    if faculty:
        sample = faculty[0]
        print(f"   Name: {sample['name']}")
        print(f"   Title: {sample['title']}")
        print(f"   Research: {sample['research_areas'][0]}")
        print(f"   Papers: {sample['publication_count']}")

    print(f"\n💰 Sample Grant:")
    if grants:
        sample = grants[0]
        print(f"   Title: {sample['title'][:80]}...")
        print(f"   PI: {sample['pi_name']}")
        print(f"   Amount: ${sample['amount']:,.2f}")

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()