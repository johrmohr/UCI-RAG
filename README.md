# UCI Research Intelligence Demo

A **demonstration** of a RAG (Retrieval-Augmented Generation) system for academic research discovery. This is a proof-of-concept showcasing how AI can help researchers find and understand academic papers through natural language queries.

## 🚀 Live Demo

**[Try the Demo →](https://uci-research-intelligence.streamlit.app/)**

Ask questions like: *"What research has been done on quantum computing?"* or *"Show me papers about machine learning in physics."*

---

## ⚠️ Important Note

**This is a DEMO system** using sample academic papers from ArXiv. It does **not** contain real UCI research data or represent actual UCI faculty research. The system demonstrates the technical architecture and capabilities of a research intelligence platform.

---

## 🏗️ How It Works (RAG Architecture)

```
User Query → Semantic Search → Retrieve Relevant Papers → AI Generation → Response
```

1. **User asks a question** in natural language
2. **System searches** through research papers using semantic similarity
3. **Retrieves relevant papers** based on the query context
4. **AI generates an answer** using the retrieved papers as context
5. **Returns response** with sources and citations

### Tech Stack
- **Frontend**: Streamlit (web interface)
- **AI Model**: Claude 3 (via AWS Bedrock)
- **Vector Database**: ChromaDB (for semantic search)
- **Embeddings**: Sentence Transformers
- **Data**: 120 research papers from ArXiv

---

## 📁 Codebase Structure

```
├── streamlit_app.py          # Main app entry point
├── frontend/app.py           # Web interface
├── rag_pipeline/             # AI processing
│   ├── rag_system.py        # Core RAG logic
│   └── search_demo.py       # Search functionality
├── data_generation/          # Data collection
│   ├── collect_arxiv_data.py # Gets papers from ArXiv
│   └── uci_research_data.json # Sample dataset (120 papers)
├── embeddings/               # Vector database
│   └── create_embeddings.py # Creates searchable vectors
└── requirements.txt          # Dependencies
```

---

## 🎯 What This Demonstrates

### RAG Pipeline Capabilities
- ✅ **Semantic Search**: Find papers by meaning, not just keywords
- ✅ **Context Retrieval**: Get relevant information from multiple sources
- ✅ **AI Generation**: Synthesize answers from retrieved content
- ✅ **Source Attribution**: Show which papers informed the answer

### Technical Implementation
- ✅ **Vector Embeddings**: Convert text to searchable vectors
- ✅ **Similarity Search**: Find most relevant content quickly
- ✅ **Prompt Engineering**: Structure AI queries effectively
- ✅ **Web Deployment**: Production-ready Streamlit app

---

## 🚀 Running Locally

```bash
# 1. Clone the repo
git clone https://github.com/johrmohr/UCI-RAG.git
cd UCI-RAG

# 2. Install dependencies
pip install -r requirements-streamlit.txt

# 3. Run the app
streamlit run streamlit_app.py
```

**Note**: For full AI features, you'll need AWS credentials configured for Claude access.

---

## 📊 Sample Dataset

The demo uses **120 research papers** from ArXiv covering:
- Quantum Physics
- High Energy Physics
- Condensed Matter
- Astrophysics
- Biological Physics

All papers are publicly available and used for demonstration purposes only.

---

## 🎓 Educational Purpose

This project demonstrates:
- How to build a **RAG system** from scratch
- **Semantic search** implementation with embeddings
- **AI integration** using modern language models
- **Web deployment** of ML applications
- **Data pipeline** development for research content

Perfect for learning about AI applications in academic research and information retrieval.

---

## 🤝 Contributing

This is an open-source demo! Feel free to:
- Fork the repository
- Experiment with the code
- Suggest improvements
- Use it as a learning resource

---

## 📄 License

MIT License - free to use and modify.

---

**Built to demonstrate RAG architecture and AI-powered research discovery** 🔬✨