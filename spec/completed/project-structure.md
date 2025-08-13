# AI News Aggregator - Project Structure Plan

## Overview

This document outlines the reorganized project structure to support the AI News Aggregator as a monorepo with three main components: Backend Services, Frontend Interface, and MCP Server.

## New Project Structure

```
ai-news-aggregator-agent/
├── README.md                    # Main project README (updated)
├── LICENSE                      # MIT License
├── .env.example                 # Example environment configuration
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Development environment setup
├── 
├── backend/                     # Python backend services (current src/)
│   ├── README.md               # Backend-specific setup instructions
│   ├── requirements.txt        # Backend dependencies
│   ├── pyproject.toml          # Python project configuration
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── agents/                 # PydanticAI news analysis agents
│   ├── fetchers/               # Content fetching from multiple sources
│   ├── services/               # Core business logic services
│   ├── models/                 # Data models and schemas
│   ├── repositories/           # Data access layer
│   └── api/                    # FastAPI routes and endpoints
│   
├── frontend/                    # Web frontend (future implementation)
│   ├── README.md               # Frontend setup instructions
│   ├── package.json            # Node.js dependencies
│   ├── index.html              # Entry point
│   ├── src/                    # Source code
│   │   ├── components/         # React/Vue components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API client services
│   │   └── utils/              # Utility functions
│   └── public/                 # Static assets
│   
├── mcp-server/                  # Model Context Protocol server
│   ├── README.md               # MCP server setup instructions
│   ├── requirements.txt        # MCP-specific dependencies
│   ├── server.py               # Main MCP server entry point
│   ├── __init__.py
│   ├── tools/                  # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── content_tools.py    # Content retrieval tools
│   │   ├── analysis_tools.py   # AI analysis and processing tools
│   │   ├── export_tools.py     # Data export and formatting tools
│   │   └── config_tools.py     # Configuration management tools
│   ├── models/                 # Pydantic models for MCP responses
│   │   ├── __init__.py
│   │   ├── content.py          # Content-related models
│   │   └── responses.py        # MCP response models
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication helpers
│   │   └── validation.py       # Input validation
│   └── tests/                  # MCP server tests
│       ├── test_tools.py
│       └── test_server.py
│   
├── shared/                      # Shared utilities and models
│   ├── __init__.py
│   ├── database/               # Database utilities
│   │   ├── __init__.py
│   │   ├── connection.py       # Database connection management
│   │   └── migrations/         # Database migrations
│   ├── models/                 # Shared Pydantic models
│   │   ├── __init__.py
│   │   ├── base.py             # Base model classes
│   │   └── common.py           # Common model definitions
│   └── utils/                  # Shared utility functions
│       ├── __init__.py
│       ├── logging.py          # Logging configuration
│       └── env.py              # Environment variable handling
│   
├── tests/                       # Test suites for all components
│   ├── backend/                # Backend tests (current tests/)
│   ├── mcp-server/             # MCP server tests
│   ├── integration/            # Cross-component integration tests
│   └── fixtures/               # Shared test fixtures
│   
├── docs/                        # Documentation
│   ├── README.md               # Documentation index
│   ├── api/                    # API documentation
│   ├── deployment/             # Deployment guides
│   └── development/            # Development guides
│   
├── spec/                        # Technical specifications
│   ├── frontend.md             # Frontend specification
│   ├── mcp-server.md           # MCP server specification
│   ├── project-structure.md    # This file
│   └── tier2-features.md       # Future features
│   
├── scripts/                     # Utility scripts
│   ├── setup.sh               # Initial project setup
│   ├── dev-setup.sh           # Development environment setup
│   ├── migrate.sh             # Database migration script
│   └── deploy.sh              # Deployment script
│   
└── venv_linux/                 # Python virtual environment (gitignored)
```

## Migration Plan

### Phase 1: Backend Reorganization
1. **Move current `src/` to `backend/`**
   - Update all import statements
   - Update configuration files
   - Update test imports

2. **Create shared utilities**
   - Extract common database utilities
   - Extract shared models
   - Create shared logging configuration

### Phase 2: MCP Server Implementation
1. **Create MCP server structure**
   - Implement basic server framework
   - Create tool implementations
   - Set up MCP-specific models

2. **Integration with existing backend**
   - Import shared models from `shared/`
   - Use existing database connections
   - Leverage existing services

### Phase 3: Frontend Preparation
1. **Create frontend structure**
   - Set up build system (Vite/Webpack)
   - Create initial component structure
   - Set up API client configuration

## Component Responsibilities

### Backend (`backend/`)
- **Purpose**: Core business logic and REST API
- **Technologies**: FastAPI, PydanticAI, SQLAlchemy
- **Responsibilities**:
  - Article fetching and processing
  - AI analysis and categorization
  - Database operations
  - REST API endpoints
  - Background task processing

### MCP Server (`mcp-server/`)
- **Purpose**: Model Context Protocol interface
- **Technologies**: MCP Python SDK, asyncio
- **Responsibilities**:
  - Expose backend functionality via MCP protocol
  - Provide tools for AI assistants
  - Handle MCP client authentication
  - Serve structured data to MCP clients

### Frontend (`frontend/`)
- **Purpose**: Web user interface
- **Technologies**: React/Vue.js, TypeScript
- **Responsibilities**:
  - User interface for content browsing
  - Dashboard and analytics
  - Configuration management
  - Real-time updates

### Shared (`shared/`)
- **Purpose**: Common utilities and models
- **Technologies**: Python, Pydantic
- **Responsibilities**:
  - Database connection management
  - Common data models
  - Logging configuration
  - Environment variable handling

## Setup Instructions Structure

### Main README.md
- Project overview and architecture
- Quick start guide for all components
- Links to component-specific READMEs
- Common environment setup

### Component READMEs
- **`backend/README.md`**: Backend-specific setup and API docs
- **`frontend/README.md`**: Frontend development setup
- **`mcp-server/README.md`**: MCP server configuration and usage

## Environment Configuration

### Development Environment Variables
```bash
# Database
DATABASE_URL=postgresql://localhost:5432/ai_news_dev
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# AI Services
GEMINI_API_KEY=your_google_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# MCP Server
MCP_SERVER_PORT=8001
MCP_LOG_LEVEL=INFO

# Backend API
API_PORT=8000
API_HOST=0.0.0.0

# Frontend
FRONTEND_PORT=3000
API_BASE_URL=http://localhost:8000

# Development
DEBUG=true
LOG_LEVEL=INFO
```

## Development Workflow

### 1. Setup All Components
```bash
# Clone and setup
git clone <repository-url>
cd ai-news-aggregator-agent

# Run setup script
./scripts/setup.sh
```

### 2. Backend Development
```bash
# Activate virtual environment
source venv_linux/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Run backend server
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 3. MCP Server Development
```bash
# Same virtual environment as backend
source venv_linux/bin/activate

# Install MCP dependencies (if different)
pip install -r mcp-server/requirements.txt

# Run MCP server
cd mcp-server
python server.py
```

### 4. Frontend Development (Future)
```bash
# Install frontend dependencies
cd frontend
npm install

# Run development server
npm run dev
```

## Testing Strategy

### Component Tests
- **Backend**: Existing test suite in `tests/backend/`
- **MCP Server**: New test suite in `tests/mcp-server/`
- **Frontend**: Future test suite in `tests/frontend/`

### Integration Tests
- Cross-component communication
- End-to-end user workflows
- MCP client-server interaction

## Deployment Considerations

### Development
- Docker Compose for all services
- Hot reload for development
- Shared database instance

### Production
- Separate containers for each component
- Load balancing for API servers
- Monitoring and logging
- Environment-specific configurations

## Benefits of This Structure

1. **Clear Separation**: Each component has distinct responsibilities
2. **Shared Resources**: Common utilities avoid duplication
3. **Independent Development**: Teams can work on components independently
4. **Scalable**: Easy to add new components or services
5. **Maintainable**: Clear organization makes maintenance easier
6. **Documentation**: Component-specific docs reduce confusion
7. **Testing**: Isolated testing with integration test coverage
8. **Deployment**: Flexible deployment options for different environments

---

This structure supports the current functionality while preparing for future growth and the addition of the MCP server and frontend components.