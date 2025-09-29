# Sample Project Specifications for Benchmark Testing
_Last updated: 2025-09-27_

See also: [Benchmark Results](../../docs/benchmark-results.md)

## Overview

This document defines three standardized project specifications used for benchmarking orchestration systems. Each specification represents a common development scenario with increasing complexity levels.

---

## Project 1: Simple Utility - CLI File Processor

### Goal Definition
Create a command-line utility for processing text files with multiple operations and comprehensive testing.

### Requirements
- **Primary Function**: CLI tool that can read, transform, and output text files
- **Operations**: Word count, character count, line count, text replacement, case conversion
- **Input/Output**: Support for file input/output and stdin/stdout
- **Configuration**: Command-line arguments with help text
- **Error Handling**: Graceful handling of missing files, permissions, invalid arguments
- **Testing**: Unit tests covering all operations with edge cases

### Technical Specifications
- **Language**: Python 3.11+
- **Dependencies**: Click or argparse for CLI, pytest for testing
- **Structure**: Single module with clear separation of concerns
- **Documentation**: README with usage examples and API documentation

### Success Criteria
1. ✅ CLI executable with `--help` functionality
2. ✅ All 5 text operations working correctly
3. ✅ Error handling for common failure scenarios
4. ✅ 90%+ test coverage with passing tests
5. ✅ Professional documentation with examples
6. ✅ Code follows PEP 8 standards

### Expected Output
```
text_processor/
├── text_processor.py      # Main CLI module
├── operations.py          # Text processing operations
├── tests/
│   ├── test_processor.py  # CLI tests
│   └── test_operations.py # Operation tests
├── README.md             # Documentation
└── requirements.txt      # Dependencies
```

### Validation Commands
```bash
# Functional validation
python text_processor.py --help
echo "Hello World" | python text_processor.py --word-count
python text_processor.py --replace "old" "new" input.txt

# Test validation
pytest tests/ -v --cov=text_processor
```

---

## Project 2: Web Service - Task Management API

### Goal Definition
Build a RESTful API for task management with user authentication, database persistence, and comprehensive testing.

### Requirements
- **API Endpoints**: CRUD operations for tasks (create, read, update, delete)
- **Authentication**: JWT-based user authentication and authorization
- **Database**: SQLite with SQLAlchemy ORM for task and user data
- **Features**: Task filtering, sorting, status updates, due dates
- **Validation**: Request/response validation with proper error codes
- **Documentation**: OpenAPI/Swagger documentation
- **Testing**: Unit tests, integration tests, API endpoint tests

### Technical Specifications
- **Framework**: FastAPI or Flask with modern Python patterns
- **Database**: SQLAlchemy ORM with SQLite for simplicity
- **Authentication**: JWT tokens with password hashing
- **Validation**: Pydantic models for request/response validation
- **Documentation**: Auto-generated API docs
- **Testing**: pytest with test database and API testing

### Success Criteria
1. ✅ Working API server with all CRUD endpoints
2. ✅ User registration and JWT authentication
3. ✅ Database persistence with proper migrations
4. ✅ Comprehensive input validation and error handling
5. ✅ API documentation accessible at `/docs`
6. ✅ 85%+ test coverage with passing integration tests
7. ✅ Professional project structure and documentation

### Expected Output
```
task_api/
├── main.py               # FastAPI application
├── models/
│   ├── __init__.py
│   ├── user.py          # User model
│   └── task.py          # Task model
├── routers/
│   ├── __init__.py
│   ├── auth.py          # Authentication endpoints
│   └── tasks.py         # Task CRUD endpoints
├── database.py          # Database configuration
├── auth.py              # Authentication utilities
├── tests/
│   ├── test_auth.py     # Authentication tests
│   ├── test_tasks.py    # Task endpoint tests
│   └── conftest.py      # Test configuration
├── README.md            # API documentation
└── requirements.txt     # Dependencies
```

### Validation Commands
```bash
# Server startup
uvicorn main:app --reload

# API validation
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

curl -X GET "http://localhost:8000/docs"  # API documentation

# Test validation
pytest tests/ -v --cov=task_api
```

---

## Project 3: Full-Stack Application - Personal Finance Tracker

### Goal Definition
Create a complete personal finance tracking application with web frontend, REST API backend, database persistence, and production deployment configuration.

### Requirements
- **Backend**: RESTful API for financial transactions, categories, budgets
- **Frontend**: React/Vue.js web interface with responsive design
- **Database**: PostgreSQL with complex relationships and data validation
- **Features**: Transaction CRUD, category management, budget tracking, reports
- **Authentication**: Multi-user support with secure session management
- **Real-time**: WebSocket updates for live transaction feeds
- **Deployment**: Docker containerization with docker-compose
- **Testing**: Full test suite including E2E tests with browser automation

### Technical Specifications
- **Backend**: FastAPI with PostgreSQL and async database operations
- **Frontend**: React with TypeScript, modern UI framework (Material-UI/Tailwind)
- **Database**: PostgreSQL with Alembic migrations
- **Real-time**: WebSocket support for live updates
- **Containerization**: Multi-stage Docker builds for production
- **Testing**: pytest + playwright for E2E testing
- **CI/CD**: GitHub Actions workflow for automated testing

### Success Criteria
1. ✅ Complete REST API with all financial operations
2. ✅ Responsive web frontend with modern UI/UX
3. ✅ PostgreSQL database with proper relationships
4. ✅ Multi-user authentication and authorization
5. ✅ Real-time updates via WebSockets
6. ✅ Docker deployment with production configuration
7. ✅ 80%+ test coverage including E2E browser tests
8. ✅ CI/CD pipeline with automated testing
9. ✅ Professional documentation and deployment guide

### Expected Output
```
finance_tracker/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── models/          # Database models
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   └── websockets/      # Real-time updates
│   ├── tests/               # Backend tests
│   ├── Dockerfile           # Backend container
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Application pages
│   │   ├── services/       # API integration
│   │   └── utils/          # Utilities
│   ├── tests/              # Frontend tests
│   ├── Dockerfile          # Frontend container
│   └── package.json
├── tests/
│   └── e2e/               # End-to-end tests
├── docker-compose.yml      # Multi-service deployment
├── .github/workflows/      # CI/CD pipeline
└── README.md              # Comprehensive documentation
```

### Validation Commands
```bash
# Full stack startup
docker-compose up -d

# Application validation
curl -X GET "http://localhost:8000/health"  # Backend health
curl -X GET "http://localhost:3000"         # Frontend access

# Test validation
# Backend tests
cd backend && pytest tests/ -v --cov=app

# Frontend tests
cd frontend && npm test

# E2E tests
pytest tests/e2e/ -v --headed
```

---

## Benchmark Testing Protocol

Refer to the canonical [benchmark protocol learnings](../../docs/benchmark-results.md#benchmark-protocol-learnings) for detailed metrics, automation commands, and reporting templates.
