"""
UCI Research Intelligence System - Configuration Module
========================================================
Centralized configuration for all system components with cost-optimized defaults
and UCI Physics department-specific settings.

Author: UCI Research Intelligence Team
Date: 2025-01-21
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import json

# Load environment variables
from dotenv import load_dotenv

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

# Determine project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Load environment variables from .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")
    print("   Using system environment variables")


class Environment(Enum):
    """Application environment modes"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


# Determine current environment
APP_ENV = Environment(os.getenv('APP_ENV', 'development').lower())
IS_PRODUCTION = APP_ENV == Environment.PRODUCTION
IS_DEVELOPMENT = APP_ENV == Environment.DEVELOPMENT


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class LogConfig:
    """Logging configuration for the application"""

    # Log level based on environment
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG' if IS_DEVELOPMENT else 'INFO')

    # Log format
    LOG_FORMAT_DETAILED = (
        '%(asctime)s | %(levelname)-8s | %(name)s | '
        '%(filename)s:%(lineno)d | %(message)s'
    )
    LOG_FORMAT_SIMPLE = '%(asctime)s | %(levelname)-8s | %(message)s'

    # Log file settings
    LOG_DIR = PROJECT_ROOT / 'logs'
    LOG_DIR.mkdir(exist_ok=True)

    LOG_FILE = LOG_DIR / f'uci_research_{APP_ENV.value}.log'
    ERROR_LOG_FILE = LOG_DIR / f'errors_{APP_ENV.value}.log'

    # Maximum log file size (10MB for cost savings)
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 3  # Keep only 3 backup files to save storage

    @classmethod
    def setup_logging(cls):
        """Configure logging for the entire application"""
        import logging.handlers

        # Create formatter
        formatter = logging.Formatter(
            cls.LOG_FORMAT_DETAILED if IS_DEVELOPMENT else cls.LOG_FORMAT_SIMPLE
        )

        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, cls.LOG_LEVEL))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler with rotation (cost-saving: limited size and backups)
        file_handler = logging.handlers.RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=cls.MAX_LOG_SIZE,
            backupCount=cls.BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            cls.ERROR_LOG_FILE,
            maxBytes=cls.MAX_LOG_SIZE,
            backupCount=cls.BACKUP_COUNT
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # Reduce verbosity of some libraries
        logging.getLogger('boto3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


# ============================================================================
# AWS CONFIGURATION
# ============================================================================

@dataclass
class AWSConfig:
    """AWS service configuration with cost-optimized defaults"""

    # Basic AWS settings
    AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')

    # S3 Configuration
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'uci-research-poc')
    S3_DATA_PREFIX = os.getenv('S3_DATA_PREFIX', 'raw-data/')
    S3_EMBEDDINGS_PREFIX = os.getenv('S3_EMBEDDINGS_PREFIX', 'embeddings/')
    S3_METADATA_PREFIX = os.getenv('S3_METADATA_PREFIX', 'metadata/')
    S3_LOGS_PREFIX = os.getenv('S3_LOGS_PREFIX', 'logs/')

    # S3 cost-saving settings
    S3_STORAGE_CLASS = 'INTELLIGENT_TIERING'  # Automatically moves to cheaper tiers
    S3_MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100MB - upload large files in parts
    S3_MAX_CONCURRENCY = 2  # Limit concurrent connections to save bandwidth
    S3_USE_ACCELERATE_ENDPOINT = False  # Don't use Transfer Acceleration (costs extra)

    # Lambda Configuration (cost-optimized)
    LAMBDA_MEMORY_SIZE = 512 if IS_PRODUCTION else 256  # MB - minimum for cost savings
    LAMBDA_TIMEOUT = 60  # seconds - keep short to avoid runaway costs
    LAMBDA_CONCURRENT_EXECUTIONS = 2  # Limit concurrent executions
    LAMBDA_RESERVED_CONCURRENCY = 0  # Don't reserve (costs extra)

    # OpenSearch Configuration (minimal for POC)
    OPENSEARCH_ENDPOINT = os.getenv('OPENSEARCH_ENDPOINT')
    OPENSEARCH_PORT = int(os.getenv('OPENSEARCH_PORT', '443'))
    OPENSEARCH_INDEX_NAME = os.getenv('OPENSEARCH_INDEX_NAME', 'uci-research-documents')

    # OpenSearch cost-saving settings
    OPENSEARCH_INSTANCE_TYPE = 't3.small.search'  # Smallest instance type
    OPENSEARCH_INSTANCE_COUNT = 1  # Single node for POC
    OPENSEARCH_DEDICATED_MASTER = False  # No dedicated master (saves cost)
    OPENSEARCH_EBS_VOLUME_SIZE = 10  # GB - minimum size
    OPENSEARCH_ZONE_AWARENESS = False  # Single AZ for cost savings

    # DynamoDB Configuration (on-demand for cost savings)
    DYNAMODB_BILLING_MODE = 'PAY_PER_REQUEST'  # Only pay for what you use
    DYNAMODB_READ_CAPACITY = 5  # If using provisioned
    DYNAMODB_WRITE_CAPACITY = 5  # If using provisioned

    # Bedrock Configuration
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')
    BEDROCK_REGION = os.getenv('BEDROCK_REGION', 'us-west-2')
    BEDROCK_MAX_TOKENS = 1000  # Limit token usage


# ============================================================================
# EMBEDDING & VECTOR SEARCH CONFIGURATION
# ============================================================================

@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation and vector search"""

    # Embedding source selection
    USE_LOCAL_EMBEDDINGS = True  # Use local sentence-transformers instead of API
    EMBEDDING_PROVIDER = 'local'  # 'local', 'openai', or 'bedrock'

    # Local embedding model (cost-effective, runs on your machine)
    LOCAL_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'  # Small, efficient model
    EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

    # Alternative models for local embeddings:
    # 'sentence-transformers/all-mpnet-base-v2': 768 dimensions, better quality
    # 'sentence-transformers/all-MiniLM-L12-v2': 384 dimensions, balanced
    # 'BAAI/bge-small-en': 384 dimensions, high quality

    # API-based embeddings (if USE_LOCAL_EMBEDDINGS = False)
    OPENAI_EMBEDDING_MODEL = 'text-embedding-3-small'  # If using OpenAI
    BEDROCK_EMBEDDING_MODEL = None  # Bedrock doesn't have dedicated embedding models

    # Batch processing settings (optimize for memory)
    EMBEDDING_BATCH_SIZE = 32 if IS_PRODUCTION else 16  # Can be higher for local models
    MAX_SEQUENCE_LENGTH = 512  # Maximum tokens per text chunk

    # Vector search configuration
    USE_OPENSEARCH = False  # Set to False to use local vector DB initially
    VECTOR_DB_PROVIDER = 'chromadb'  # 'chromadb', 'opensearch', or 'pinecone'

    # Vector search settings
    VECTOR_SEARCH_TOP_K = 10  # Number of results to return
    SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score
    USE_GPU = False  # Set True if you have Apple Silicon MPS or CUDA

    # ChromaDB settings (local vector DB - recommended for POC)
    CHROMA_PERSIST_DIRECTORY = str(PROJECT_ROOT / 'data' / 'chroma')
    CHROMA_COLLECTION_NAME = 'uci_physics_research'

    # OpenSearch settings (when USE_OPENSEARCH = True)
    OPENSEARCH_ENDPOINT = os.getenv('OPENSEARCH_ENDPOINT', '')
    OPENSEARCH_INDEX_NAME = os.getenv('OPENSEARCH_INDEX_NAME', 'uci-research-documents')

    # Pinecone settings (alternative cloud vector DB)
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp')
    PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'uci-research')
    PINECONE_METRIC = 'cosine'  # or 'euclidean', 'dotproduct'


# ============================================================================
# DOCUMENT PROCESSING CONFIGURATION
# ============================================================================

@dataclass
class DocumentConfig:
    """Configuration for document processing and chunking"""

    # Chunking settings (optimized for context and cost)
    CHUNK_SIZE = 1000  # Characters per chunk (balanced for context)
    CHUNK_OVERLAP = 200  # Overlap between chunks for context continuity
    MIN_CHUNK_SIZE = 100  # Minimum chunk size to keep

    # Document splitting strategies
    SPLIT_BY = 'recursive'  # 'recursive', 'sentence', 'paragraph', 'page'
    SEPARATORS = ['\n\n', '\n', '. ', ' ', '']  # For recursive splitting

    # File processing limits (cost savings)
    MAX_FILE_SIZE_MB = 50  # Maximum file size to process
    MAX_PAGES_PER_PDF = 100  # Limit PDF processing
    MAX_FILES_PER_BATCH = 10  # Process files in small batches

    # Supported file types
    SUPPORTED_EXTENSIONS = [
        '.pdf', '.txt', '.md', '.tex',  # Documents
        '.docx', '.doc',  # Word documents
        '.html', '.xml',  # Web content
        '.json', '.csv',  # Data files
    ]

    # Text extraction settings
    EXTRACT_TABLES = True
    EXTRACT_IMAGES = False  # Disabled for cost savings
    OCR_ENABLED = False  # OCR is expensive, disable for POC


# ============================================================================
# UCI PHYSICS DEPARTMENT CONFIGURATION
# ============================================================================

@dataclass
class UCIPhysicsConfig:
    """UCI Physics Department specific configuration"""

    # Department Information
    DEPARTMENT_NAME = "Department of Physics and Astronomy"
    UNIVERSITY = "University of California, Irvine"
    DEPARTMENT_URL = "https://www.physics.uci.edu/"

    # Research Areas (main focus areas for the department)
    RESEARCH_AREAS = [
        "Astrophysics and Cosmology",
        "Condensed Matter Physics",
        "Particle Physics",
        "Plasma Physics",
        "Biological Physics",
        "Quantum Information Science",
        "Atomic, Molecular, and Optical Physics",
        "Theoretical Physics",
        "Experimental High Energy Physics",
        "Gravitational Physics",
    ]

    # Common Grant Sources for Physics Research
    GRANT_SOURCES = [
        "NSF (National Science Foundation)",
        "DOE (Department of Energy)",
        "NASA",
        "NIH (National Institutes of Health)",
        "DARPA",
        "ONR (Office of Naval Research)",
        "AFOSR (Air Force Office of Scientific Research)",
        "ARO (Army Research Office)",
        "Gordon and Betty Moore Foundation",
        "Simons Foundation",
        "Templeton Foundation",
        "Research Corporation for Science Advancement",
    ]

    # Research Keywords (for better search and categorization)
    RESEARCH_KEYWORDS = [
        # Particle Physics
        "hadron", "quark", "lepton", "boson", "fermion", "neutrino",
        "dark matter", "dark energy", "higgs", "supersymmetry",

        # Condensed Matter
        "superconductor", "semiconductor", "nanostructure", "graphene",
        "topological insulator", "quantum hall", "spin", "magnetism",

        # Astrophysics
        "galaxy", "black hole", "neutron star", "cosmology", "redshift",
        "gravitational waves", "exoplanet", "pulsar", "quasar",

        # Quantum
        "quantum computing", "qubit", "entanglement", "coherence",
        "quantum optics", "quantum cryptography", "bell inequality",

        # Methods
        "spectroscopy", "interferometry", "cryogenics", "vacuum",
        "laser", "detector", "accelerator", "telescope",
    ]

    # Common Journals for Physics Publications
    PREFERRED_JOURNALS = [
        "Physical Review Letters",
        "Physical Review D",
        "Physical Review B",
        "Nature Physics",
        "Science",
        "Nature",
        "Applied Physics Letters",
        "Journal of High Energy Physics",
        "Astrophysical Journal",
        "Nuclear Physics B",
        "Physics Letters B",
        "Review of Modern Physics",
    ]

    # ArXiv Categories relevant to Physics
    ARXIV_CATEGORIES = [
        "hep-ph",  # High Energy Physics - Phenomenology
        "hep-th",  # High Energy Physics - Theory
        "hep-ex",  # High Energy Physics - Experiment
        "cond-mat",  # Condensed Matter
        "quant-ph",  # Quantum Physics
        "astro-ph",  # Astrophysics
        "nucl-th",  # Nuclear Theory
        "gr-qc",  # General Relativity and Quantum Cosmology
        "physics",  # General Physics
    ]

    # Faculty size (approximate for resource planning)
    ESTIMATED_FACULTY_COUNT = 50
    ESTIMATED_GRAD_STUDENTS = 150
    ESTIMATED_POSTDOCS = 30


# ============================================================================
# RAG (RETRIEVAL AUGMENTED GENERATION) CONFIGURATION
# ============================================================================

@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""

    # LLM Selection for chat/generation
    USE_BEDROCK_FOR_CHAT = True  # Use AWS Bedrock for chat responses
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'bedrock')  # 'bedrock', 'openai', 'anthropic'

    # Bedrock configuration (for chat responses only, not embeddings)
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')
    BEDROCK_REGION = os.getenv('BEDROCK_REGION', 'us-west-2')
    # Claude 3 models available on Bedrock:
    # 'anthropic.claude-3-haiku-20240307-v1:0' - Fastest and cheapest
    # 'anthropic.claude-3-sonnet-20240229-v1:0' - Balanced
    # 'anthropic.claude-3-opus-20240229-v1:0' - Most capable but expensive

    # Alternative LLM providers (if not using Bedrock)
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')  # If using OpenAI
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku')  # If using Anthropic API

    # Token limits (control costs)
    MAX_PROMPT_TOKENS = 2000
    MAX_RESPONSE_TOKENS = 500
    TEMPERATURE = 0.7
    TOP_P = 0.9

    # Context window management
    MAX_CONTEXT_LENGTH = 4000  # Total tokens for context
    MAX_RETRIEVED_CHUNKS = 5  # Number of chunks to include

    # Prompt templates
    SYSTEM_PROMPT = """You are an AI research assistant for the UCI Physics Department.
    Your role is to help researchers find relevant papers, summarize research,
    and answer questions about physics research. Be accurate, concise, and cite sources."""

    # Cache settings (reduce API calls)
    ENABLE_RESPONSE_CACHE = True
    CACHE_TTL_SECONDS = 3600  # 1 hour cache
    CACHE_MAX_SIZE = 100  # Maximum cached responses

    # Embedding settings (using local embeddings, not LLM provider)
    USE_LOCAL_EMBEDDINGS = True  # Always use local embeddings for cost savings
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'  # Local model


# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

@dataclass
class AppConfig:
    """General application configuration"""

    # Application metadata
    APP_NAME = "UCI Research Intelligence System"
    APP_VERSION = "0.1.0"
    APP_DESCRIPTION = "AI-powered research discovery for UCI Physics"

    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    API_WORKERS = 2 if IS_PRODUCTION else 1  # Minimal workers for cost
    API_RELOAD = IS_DEVELOPMENT
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8501"]

    # Frontend Configuration
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')
    STREAMLIT_THEME = 'light'

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24

    # Rate limiting (prevent abuse)
    RATE_LIMIT_REQUESTS = 100  # Per hour
    RATE_LIMIT_EMBEDDINGS = 50  # Per hour
    RATE_LIMIT_LLM_CALLS = 20  # Per hour

    # File upload limits
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '10'))
    ALLOWED_UPLOAD_EXTENSIONS = DocumentConfig.SUPPORTED_EXTENSIONS

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./uci_research.db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Feature Flags
    ENABLE_CACHING = True
    ENABLE_METRICS = True
    ENABLE_TRACING = IS_DEVELOPMENT
    ENABLE_COST_MONITORING = False  # Disabled for POC
    USE_OPENSEARCH = False  # Use local vector DB for POC
    USE_LOCAL_EMBEDDINGS = True  # Use local embeddings for cost savings


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================

class Config:
    """Main configuration class that combines all configurations"""

    def __init__(self):
        self.env = APP_ENV
        self.is_production = IS_PRODUCTION
        self.is_development = IS_DEVELOPMENT

        # Initialize all configuration sections
        self.aws = AWSConfig()
        self.embedding = EmbeddingConfig()
        self.document = DocumentConfig()
        self.uci_physics = UCIPhysicsConfig()
        self.rag = RAGConfig()
        self.app = AppConfig()
        self.log = LogConfig()

        # Setup logging
        self.log.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Configuration loaded for environment: {self.env.value}")

    def get_config_dict(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return {
            'environment': self.env.value,
            'aws': self.aws.__dict__,
            'embedding': self.embedding.__dict__,
            'document': self.document.__dict__,
            'rag': self.rag.__dict__,
            'app': self.app.__dict__,
            'uci_physics': self.uci_physics.__dict__,
        }

    def save_config(self, filepath: str = "config_snapshot.json"):
        """Save current configuration to a JSON file"""
        config_dict = self.get_config_dict()
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
        self.logger.info(f"Configuration saved to {filepath}")

    def validate_config(self) -> bool:
        """Validate that required configuration values are set"""
        errors = []

        # Check critical AWS settings
        if not self.aws.AWS_REGION:
            errors.append("AWS_REGION not set")
        if not self.aws.S3_BUCKET_NAME:
            errors.append("S3_BUCKET_NAME not set")

        # Check API keys if using external services
        if self.rag.LLM_PROVIDER == 'openai' and not os.getenv('OPENAI_API_KEY'):
            errors.append("OPENAI_API_KEY not set for OpenAI provider")

        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            return False

        self.logger.info("Configuration validation passed")
        return True


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Create a singleton configuration instance
config = Config()

# Export commonly used configurations
aws_config = config.aws
embedding_config = config.embedding
document_config = config.document
uci_physics_config = config.uci_physics
rag_config = config.rag
app_config = config.app


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_config() -> Config:
    """Get the configuration singleton"""
    return config


def print_config():
    """Print current configuration for debugging"""
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    print("\n" + "="*60)
    print("CURRENT CONFIGURATION")
    print("="*60)
    pp.pprint(config.get_config_dict())
    print("="*60 + "\n")


# Run validation when module is imported
if not config.validate_config():
    print("⚠️  WARNING: Configuration validation failed. Check logs for details.")

if __name__ == "__main__":
    print_config()