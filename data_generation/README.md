# UCI Research Intelligence

A comprehensive research intelligence system for collecting, processing, and analyzing academic research data from UCI faculty and researchers.

## Overview

This project collects and processes research papers from ArXiv and NSF grant data to create a comprehensive dataset of UCI research activities. The system focuses on quantum physics, high-energy physics, condensed matter physics, and related fields.

## Dataset

### Current Data (uci_research_data.json)
- **120 research papers** (duplicates removed)
- **3 faculty members** tracked
- **12 NSF grants** included
- **Research areas**: quantum physics, high-energy theory, condensed matter, general relativity, biophysics, astrophysics
- **Date range**: 2022-2024

### Data Sources
- **ArXiv API**: Academic papers and preprints
- **NSF Award API**: Grant funding information

## Files

### Data Files
- `uci_research_data.json` - Main dataset (120 papers, cleaned)
- `duplicate_removal_report.json` - Report of duplicate entries found and removed
- `demo_queries.json` - Sample queries for testing the dataset

### Scripts
- `collect_arxiv_data.py` - Collects research papers from ArXiv API
- `upload_real_data_to_s3.py` - Uploads data to AWS S3 for cloud storage
- `generate_demo_queries.py` - Generates sample queries for the dataset
- `inspect_collected_data.py` - Data analysis and inspection utilities

### Metadata
- `upload_metadata.json` - Upload tracking information

## Data Processing Features

### Duplicate Removal
The dataset has been cleaned to remove duplicate entries based on ArXiv IDs:
- Original count: 132 papers
- Final count: 120 papers
- Duplicates removed: 12 entries

### Data Structure
Each paper entry includes:
```json
{
  "arxiv_id": "unique identifier",
  "title": "paper title",
  "abstract": "paper abstract",
  "published": "publication date",
  "authors": ["list of authors"],
  "categories": ["research categories"],
  "pdf_link": "link to PDF",
  "abs_link": "link to abstract",
  "source": "data source",
  "document_type": "research_paper"
}
```

## Usage

### Data Access
The cleaned research data is available in `uci_research_data.json` and can be:
- Loaded into analytics tools
- Used for research trend analysis
- Integrated into RAG (Retrieval-Augmented Generation) systems
- Queried for specific research topics

### Sample Queries
See `demo_queries.json` for example queries including:
- Faculty-specific research
- Topic-based searches
- Grant-related inquiries
- Cross-disciplinary research

## Research Areas Covered

- **Quantum Physics** (quant-ph)
- **High Energy Physics - Theory** (hep-th)
- **Condensed Matter Physics** (cond-mat)
- **General Relativity** (gr-qc)
- **Biological Physics** (physics.bio-ph)
- **Astrophysics** (astro-ph)

## Technical Details

- **File Size**: ~236KB (cleaned dataset)
- **Format**: JSON with metadata and structured paper entries
- **Last Updated**: September 26, 2025
- **Duplicate Cleaning**: Automated script with backup preservation

## Cloud Integration

The project includes AWS S3 integration for cloud storage and distribution of the research dataset.

---

*This dataset is part of the UCI Research Intelligence initiative to enhance academic research discovery and analysis.*
