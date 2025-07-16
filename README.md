# AI News Aggregator

An intelligent news aggregation system that fetches, analyzes, and curates AI/ML content from multiple sources using PydanticAI agents and semantic deduplication.

## 🚀 Features

- **Multi-Source Fetching**: Aggregates content from ArXiv, HackerNews, and RSS feeds
- **AI-Powered Analysis**: Uses Google Gemini via PydanticAI for content relevance scoring
- **Semantic Deduplication**: Vector embeddings with 85% similarity threshold for duplicate detection
- **FastAPI Backend**: RESTful API with async/await patterns and background tasks
- **Vector Search**: Supabase with pgvector for efficient similarity search
- **Rate Limiting**: Respects API limits (ArXiv 3s delay, HackerNews 1 req/sec)
- **Structured Data**: Pydantic models with validation and type safety

## 🏗️ Architecture

```
src/
├── agents/           # PydanticAI news analysis agents
│   ├── news_agent.py # Main analysis agent with structured output
│   └── prompts.py    # System prompts for AI analysis
├── fetchers/         # Content fetching from multiple sources
│   ├── base.py       # Abstract base fetcher with retry logic
│   ├── arxiv_fetcher.py      # ArXiv API integration
│   ├── hackernews_fetcher.py # HackerNews API integration
│   ├── rss_fetcher.py        # RSS feed parsing
│   └── factory.py    # Fetcher factory pattern
├── services/         # Core business logic services
│   ├── embeddings.py # HuggingFace embeddings generation
│   └── deduplication.py # Semantic similarity detection
├── models/           # Data models and schemas
│   ├── articles.py   # Core article and digest models
│   ├── schemas.py    # API request/response schemas
│   └── database.py   # SQLAlchemy database models
├── repositories/     # Data access layer
│   └── articles.py   # Article CRUD operations
├── api/              # FastAPI routes and endpoints
│   ├── routes.py     # API endpoints
│   └── dependencies.py # Dependency injection
├── config.py         # Configuration management
└── main.py          # FastAPI application entry point
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Supabase account with pgvector extension
- Google Gemini API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-news-aggregator-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv_linux
   source venv_linux/bin/activate  # On Windows: venv_linux\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Configure database**
   ```bash
   # Run the SQL migration in your Supabase dashboard
   cat migrations/001_initial_schema.sql
   ```

### Environment Configuration

Required environment variables in `.env`:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# AI Configuration  
GEMINI_API_KEY=your_google_gemini_api_key

# Optional Configuration
SIMILARITY_THRESHOLD=0.85
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOG_LEVEL=INFO
BATCH_SIZE=10
MAX_CONCURRENT_REQUESTS=5
```

## 🚀 Usage

### Starting the API Server

```bash
source venv_linux/bin/activate
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### API Endpoints

#### Health Check
```http
GET /health
```
Returns system status and database connectivity.

#### List Articles
```http
GET /articles?limit=10&offset=0&source=arxiv&min_relevance_score=50&since_hours=24
```
Retrieve paginated articles with filtering options.

#### Get Article
```http
GET /articles/{article_id}
```
Fetch a specific article by ID.

#### Trigger Fetch
```http
POST /webhook/fetch
Content-Type: application/json

{
  "sources": ["arxiv", "hackernews", "rss"]
}
```
Manually trigger article fetching from specified sources.

#### Get Statistics
```http
GET /stats
```
Retrieve aggregated statistics about articles and system performance.

#### Analyze Article
```http
POST /articles/{article_id}/analyze
```
Re-run AI analysis on a specific article.

#### Get Latest Digest
```http
GET /digest/latest
```
Retrieve the latest daily digest of top articles.

## 🔄 Data Flow

1. **Fetching**: Background tasks collect articles from ArXiv, HackerNews, and RSS feeds
2. **Analysis**: PydanticAI agent analyzes each article for AI/ML relevance (0-100 score)
3. **Embedding**: Generate 384-dimension vectors using sentence-transformers
4. **Deduplication**: Compare embeddings with 85% cosine similarity threshold
5. **Storage**: Store unique articles in Supabase with vector indexes
6. **API**: Serve processed articles through FastAPI endpoints

## 🧠 AI Analysis

The system uses Google Gemini through PydanticAI to analyze articles:

```python
# Analysis output structure
class NewsAnalysis(BaseModel):
    summary: str = Field(..., description="Concise summary")
    relevance_score: int = Field(..., ge=0, le=100)
    categories: List[str] = Field(..., description="AI/ML categories")
    key_points: List[str] = Field(..., description="Main takeaways")
    reasoning: str = Field(..., description="Score justification")
```

Articles scoring below the relevance threshold (default 50) are filtered out.

## 🔍 Vector Search & Deduplication

- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Similarity**: Cosine similarity with 85% threshold
- **Index**: HNSW index in Supabase pgvector for fast retrieval
- **Caching**: In-memory embedding cache for performance

## 📊 Monitoring & Observability

### Health Monitoring
- Database connectivity checks
- Fetcher status monitoring
- Article processing statistics
- Error rate tracking

### Logging
Structured logging with configurable levels:
```python
# Key log events
- Article fetch attempts and results
- AI analysis outcomes
- Deduplication decisions
- API request/response cycles
- Error conditions and retries
```

## 🧪 Testing

### Running Tests
```bash
source venv_linux/bin/activate
pytest tests/ -v
```

### Test Structure
```
tests/
├── test_models/      # Pydantic model validation tests
├── test_services/    # Business logic tests
├── test_fetchers/    # External API integration tests
└── test_api/        # FastAPI endpoint tests
```

### Test Coverage
- Unit tests for core models and services
- Integration tests for external APIs
- API endpoint testing with mock data
- Error handling and edge cases

## 🔧 Development

### Code Quality
```bash
# Type checking
mypy src/

# Linting and formatting
ruff check src/ --fix

# Run tests
pytest tests/
```

### Key Patterns

**Error Handling**: Circuit breaker pattern with exponential backoff
```python
# Fetcher retry logic with exponential backoff
for attempt in range(self.max_retries):
    try:
        response = await self._make_request(url)
        return response
    except Exception as e:
        if attempt < self.max_retries - 1:
            await asyncio.sleep(2 ** attempt)
```

**Rate Limiting**: Source-specific rate limiting
```python
# ArXiv requires 3-second delays
self.client = arxiv.Client(delay_seconds=3.0)

# HackerNews allows 1 request per second
await asyncio.sleep(1.0)
```

**Async Processing**: Concurrent operations with proper resource management
```python
# Batch processing with semaphore
semaphore = asyncio.Semaphore(max_concurrent)
tasks = [self._process_with_semaphore(item, semaphore) for item in items]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## 📈 Performance Considerations

- **Batch Processing**: Articles processed in configurable batches (default: 10)
- **Connection Pooling**: Async HTTP clients with connection reuse
- **Embedding Caching**: In-memory cache for generated embeddings
- **Database Indexes**: HNSW vector indexes for fast similarity search
- **Background Tasks**: Non-blocking article processing via FastAPI background tasks

## 🔐 Security

- **API Keys**: Secure handling via environment variables
- **Input Validation**: Pydantic models validate all inputs
- **SQL Injection**: Protected via SQLAlchemy ORM
- **Rate Limiting**: Built-in protection against API abuse
- **CORS**: Configurable CORS policies for API access

## 📚 Dependencies

### Core Dependencies
- **FastAPI**: Modern web framework for APIs
- **PydanticAI**: Structured AI agent framework
- **Supabase**: Backend-as-a-service with pgvector
- **SQLAlchemy**: Python SQL toolkit and ORM
- **sentence-transformers**: Embedding model library
- **arxiv**: ArXiv API client library
- **feedparser**: RSS feed parsing library

### Development Dependencies
- **pytest**: Testing framework
- **mypy**: Static type checking
- **ruff**: Fast Python linter and formatter
- **uvicorn**: ASGI server for FastAPI

## 🚦 Status

✅ **Core Features Implemented**
- Multi-source content fetching
- AI-powered content analysis
- Semantic deduplication
- RESTful API with FastAPI
- Vector search with Supabase
- Comprehensive error handling

🔄 **In Development**
- Rate limiter service
- Digest generation agent
- Text-to-speech integration
- Scheduled fetching automation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions and support:
- Create an issue in the GitHub repository
- Check the [documentation](docs/) for detailed guides
- Review the [API documentation](http://localhost:8000/docs) when running locally