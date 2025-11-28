# Job Application Tracker

A full-stack web application for tracking job applications with intelligent job scraping capabilities from multiple job boards. Built with React, FastAPI, PostgreSQL, and Celery.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/react-18.2.0-blue.svg)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Functionality
- **Job Application Management**: Track applications with multiple status stages (Applied, Phone Screen, Technical Interview, On-site, Offer, Rejected, Bookmarked)
- **Multi-Site Job Scraping**: Automatically scrape job postings from LinkedIn, Indeed, Glassdoor, and Google Jobs
- **Intelligent URL Parsing**: Auto-extract job details from job posting URLs using NLP
- **Advanced Search & Filtering**: Search by title, company, location, skills, and relevance
- **Skills Analytics**: Track and analyze top skills across job postings
- **Resume Management**: Upload and manage multiple resume versions
- **Secure Authentication**: OAuth2 integration with Auth0

### Technical Features
- **Asynchronous Processing**: Background job scraping with Celery task queue
- **Real-time Updates**: Poll-based status updates for scraping tasks
- **Responsive UI**: Modern, mobile-friendly interface with TailwindCSS
- **RESTful API**: Well-documented API endpoints with automatic OpenAPI docs
- **Database Migrations**: Version-controlled schema changes with Alembic
- **Containerized Deployment**: Docker Compose orchestration for easy deployment

## Architecture
This project follows **SOLID principles** and implements multiple **design patterns** for maintainability and scalability.

### Quick Architecture Overview

- **Layered Architecture**: Presentation → Business Logic → Data Access
- **Design Patterns**: Strategy, Repository, Factory, Dependency Injection, Facade
- **SOLID Principles**: All five principles implemented throughout
- **Dependency Inversion**: Services depend on interfaces, not concrete implementations

**📖 For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md)**

### Key Architectural Features

- **Strategy Pattern** for pluggable job scrapers
- **Repository Pattern** for abstracted data access
- **Factory Pattern** for scraper creation
- **Dependency Injection Container** for loose coupling
- **Custom Exception Hierarchy** for better error handling
- **Interface Segregation** for focused service contracts



## Tech Stack

### Frontend
- **React 18.2** - UI framework
- **React Router v6** - Client-side routing
- **Vite 5.1** - Build tool and dev server
- **TailwindCSS 3.2** - Utility-first CSS framework
- **Axios** - HTTP client
- **Auth0 React SDK** - Authentication
- **Lucide React** - Icon library

### Backend
- **FastAPI 0.104** - Modern async web framework
- **SQLAlchemy 2.0** - ORM and database toolkit
- **Alembic 1.12** - Database migrations
- **Pydantic v2** - Data validation
- **Python-Jose** - JWT handling
- **Celery 5.3** - Distributed task queue
- **BeautifulSoup4** - Web scraping
- **spaCy 3.7** - Natural language processing
- **python-jobspy** - Job board scraping library

### Infrastructure
- **PostgreSQL 13** - Relational database
- **Redis 6** - Cache and message broker
- **Docker & Docker Compose** - Containerization
- **Uvicorn** - ASGI server
- **GitHub Actions** - CI/CD pipeline

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (20.10+) and **Docker Compose** (1.29+)
- **Node.js** (16+) and **npm** (8+) - for local frontend development
- **Python** (3.9+) - for local backend development
- **Git** - version control

### Optional
- **Auth0 Account** - for authentication (free tier available)
- **PostgreSQL** (13+) - if running without Docker
- **Redis** (6+) - if running without Docker

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/job-app-tracker.git
cd job-app-tracker
```

### 2. Set Up Environment Variables

#### Backend Configuration
Create `/backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/jobtracker

# Redis
REDIS_URL=redis://redis:6379/0

# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_API_AUDIENCE=https://your-api-audience
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Application
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Frontend Configuration
Create `/frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=https://your-api-audience
VITE_AUTH0_REDIRECT_URI=http://localhost:3000
```

### 3. Docker Deployment (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Local Development Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In a separate terminal, start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# In another terminal, start Celery beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# The app will be available at http://localhost:5173
```

## Configuration

### Auth0 Setup

1. **Create an Auth0 Account**: Sign up at [auth0.com](https://auth0.com)

2. **Create an Application**:
   - Go to Applications → Create Application
   - Choose "Single Page Application"
   - Note your Domain and Client ID

3. **Configure Application**:
   - **Allowed Callback URLs**: `http://localhost:3000, http://localhost:5173`
   - **Allowed Logout URLs**: `http://localhost:3000, http://localhost:5173`
   - **Allowed Web Origins**: `http://localhost:3000, http://localhost:5173`

4. **Create an API**:
   - Go to Applications → APIs → Create API
   - Set an identifier (e.g., `https://job-tracker-api`)
   - Note your API Audience

5. **Update Environment Variables**: Use the values from Auth0 in your `.env` files

### Database Configuration

The default PostgreSQL configuration in `docker-compose.yml`:

```yaml
POSTGRES_USER: postgres
POSTGRES_PASSWORD: password
POSTGRES_DB: jobtracker
```

**⚠️ Security Best Practice**: Change these credentials in production and use strong passwords.

### Celery Configuration

Configure job scraping intervals in `/backend/app/tasks/job_scraper.py`:

```python
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run job scraping every day at 9 AM
    sender.add_periodic_task(
        crontab(hour=9, minute=0),
        periodic_scrape_jobs.s(),
    )
```

## Usage

### Basic Workflow

1. **Sign Up/Login**: Click "Login" and authenticate with Auth0
2. **Add a Job Application**:
   - Click "Add Job" button
   - Paste a job URL for auto-extraction OR enter details manually
   - Click "Save"
3. **Scrape Jobs**:
   - Navigate to "Find Jobs" section
   - Enter search terms (e.g., "Software Engineer")
   - Select location and job boards
   - Click "Search Jobs"
   - Wait for results and add interesting jobs to your tracker
4. **Manage Applications**:
   - Update status as you progress through interview stages
   - Add notes about interviews
   - Filter by status or search by company/title
5. **View Analytics**:
   - Check "Top Skills" to see most in-demand skills

### Advanced Features

#### Bulk Job Scraping

```bash
# Using the API directly
curl -X POST "http://localhost:8000/api/jobs/scrape" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": ["Python Developer", "Backend Engineer"],
    "location": "San Francisco, CA",
    "num_jobs": 50,
    "sites": ["linkedin", "indeed", "glassdoor"],
    "hours_old": 72,
    "fetch_description": true
  }'
```

#### Resume Management

```bash
# Upload a resume
curl -X POST "http://localhost:8000/api/resumes/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/resume.pdf" \
  -F "title=Software Engineer Resume" \
  -F "tags=python,backend,api"
```

## API Documentation

### Interactive API Docs

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Jobs

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/jobs/` | List all jobs | No |
| POST | `/api/jobs/` | Create a job | Yes |
| GET | `/api/jobs/{id}` | Get specific job | Yes |
| PUT | `/api/jobs/{id}` | Update a job | Yes |
| DELETE | `/api/jobs/{id}` | Delete a job | Yes |
| POST | `/api/jobs/parse-url` | Parse job URL | Yes |
| POST | `/api/jobs/scrape` | Start scraping task | Yes |
| GET | `/api/jobs/scrape/{task_id}` | Check scrape status | Yes |
| GET | `/api/jobs/top-skills` | Get top skills | No |

#### Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

## Development

### Project Structure

```
job-app-tracker/
├── backend/
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   ├── auth/             # Authentication logic
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── tasks/            # Celery tasks
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   └── main.py           # FastAPI app
│   ├── migrations/           # Alembic migrations
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   ├── App.jsx           # Main app component
│   │   └── main.jsx          # Entry point
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite configuration
│   └── Dockerfile
├── docker-compose.yml        # Docker orchestration
└── README.md
```

### Code Style and Best Practices

#### Backend (Python)

- **PEP 8**: Follow Python style guide
- **Type Hints**: Use type annotations for function parameters and returns
- **Async/Await**: Use async functions for I/O-bound operations
- **Pydantic Models**: Validate all input/output data
- **Error Handling**: Use FastAPI's HTTPException for errors

```python
# Good example
from typing import List, Optional
from fastapi import HTTPException

async def get_jobs(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Job]:
    """
    Retrieve jobs for a user with optional filtering.

    Args:
        user_id: The user's unique identifier
        status: Optional status filter
        limit: Maximum number of results

    Returns:
        List of Job objects

    Raises:
        HTTPException: If user is not found
    """
    try:
        # Implementation
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Frontend (React)

- **Functional Components**: Use hooks instead of class components
- **Component Organization**: One component per file
- **Props Destructuring**: Destructure props in function parameters
- **Error Boundaries**: Implement error handling
- **Loading States**: Always show loading indicators

```jsx
// Good example
import { useState, useEffect } from 'react';
import { jobService } from '../services/api';

export const JobList = ({ userId, status }) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        const data = await jobService.getJobs({ status });
        setJobs(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, [status]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div>
      {jobs.map(job => <JobCard key={job.id} job={job} />)}
    </div>
  );
};
```

### Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Adding New Features

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Backend Changes**:
   - Add model in `/backend/app/models/`
   - Create schema in `/backend/app/schemas/`
   - Implement service in `/backend/app/services/`
   - Add routes in `/backend/app/api/` or `/backend/app/main.py`
   - Create migration: `alembic revision --autogenerate`

3. **Frontend Changes**:
   - Create components in `/frontend/src/components/`
   - Add API service methods in `/frontend/src/services/api.js`
   - Update routes in `/frontend/src/App.jsx` if needed

4. **Commit Changes**:
   ```bash
   git add .
   git commit -m "feat: description of your feature"
   git push origin feature/your-feature-name
   ```

## Testing

### Backend Testing

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_jobs.py
```

### Frontend Testing

```bash
cd frontend

# Install test dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### Example Test Structure

#### Backend Test (`/backend/tests/test_jobs.py`)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_job():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/jobs/",
            json={
                "title": "Software Engineer",
                "company": "Tech Corp",
                "status": "applied"
            },
            headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Software Engineer"
```

#### Frontend Test (`/frontend/src/components/JobCard.test.jsx`)

```javascript
import { render, screen } from '@testing-library/react';
import { JobCard } from './JobCard';

test('renders job card with title and company', () => {
  const job = {
    id: 1,
    title: 'Software Engineer',
    company: 'Tech Corp',
    status: 'applied'
  };

  render(<JobCard job={job} />);

  expect(screen.getByText('Software Engineer')).toBeInTheDocument();
  expect(screen.getByText('Tech Corp')).toBeInTheDocument();
});
```

## Deployment

### Production Considerations

#### Environment Variables

**⚠️ Security**: Never commit `.env` files. Use environment variable management:

- **Docker Secrets**: For Docker Swarm
- **Kubernetes Secrets**: For K8s deployments
- **Cloud Provider Secrets**: AWS Secrets Manager, Azure Key Vault, GCP Secret Manager

#### Database

- **Connection Pooling**: Configure SQLAlchemy pool size
- **Backups**: Schedule regular database backups
- **Migrations**: Test migrations on staging before production

#### Security Checklist

- [ ] Change all default passwords
- [ ] Use HTTPS (TLS/SSL) for all connections
- [ ] Enable CORS only for trusted domains
- [ ] Set secure Auth0 callback URLs
- [ ] Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- [ ] Enable rate limiting on API endpoints
- [ ] Keep dependencies updated
- [ ] Use environment-specific configuration
- [ ] Enable database connection encryption
- [ ] Set up monitoring and alerting

### Docker Production Deployment

1. **Update `docker-compose.prod.yml`**:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    restart: unless-stopped
```

2. **Deploy**:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment Options

#### AWS
- **ECS/Fargate**: Container orchestration
- **RDS PostgreSQL**: Managed database
- **ElastiCache Redis**: Managed Redis
- **S3**: Resume file storage
- **CloudFront**: CDN for frontend

#### Google Cloud Platform
- **Cloud Run**: Serverless containers
- **Cloud SQL**: Managed PostgreSQL
- **Memorystore**: Managed Redis
- **Cloud Storage**: File storage

#### Heroku (Quick Start)

```bash
# Install Heroku CLI
heroku login

# Create app
heroku create job-tracker-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Deploy
git push heroku main
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms**: `could not connect to server: Connection refused`

**Solutions**:
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database credentials in `.env`
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Wait for database to be ready (check logs: `docker-compose logs db`)

#### 2. Celery Workers Not Processing Tasks

**Symptoms**: Jobs stuck in "pending" state

**Solutions**:
- Check Celery worker is running: `docker-compose ps celery`
- Verify Redis connection: `docker-compose logs redis`
- Check Celery logs: `docker-compose logs celery`
- Ensure `REDIS_URL` is correct in backend `.env`

#### 3. Auth0 Authentication Failing

**Symptoms**: `401 Unauthorized` or redirect loops

**Solutions**:
- Verify Auth0 credentials in `.env` files
- Check callback URLs in Auth0 dashboard match your app URLs
- Ensure API audience is configured correctly
- Clear browser cache and cookies
- Check token expiration settings

#### 4. Job Scraping Returns No Results

**Symptoms**: Scraping completes but returns empty array

**Solutions**:
- Some job boards may block scraping (use VPN)
- Verify `python-jobspy` is installed correctly
- Check search terms are valid
- Try fewer job boards at once
- Increase `hours_old` parameter for broader results

#### 5. Frontend Can't Reach Backend

**Symptoms**: Network errors or CORS issues

**Solutions**:
- Verify `VITE_API_URL` in frontend `.env`
- Check backend is running: `curl http://localhost:8000/api/health`
- Verify CORS origins in backend `.env`: `ALLOWED_ORIGINS`
- Check browser console for specific error messages

### Debug Mode

Enable debug logging:

**Backend**:
```bash
# In backend/.env
LOG_LEVEL=DEBUG

# Or when running directly
uvicorn app.main:app --reload --log-level debug
```

**Frontend**:
```bash
# In browser console
localStorage.setItem('debug', 'app:*')
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/job-app-tracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/job-app-tracker/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/job-app-tracker/wiki)

## Contributing

We welcome contributions! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'feat: add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, semicolons, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update the README if you change functionality
5. Request review from maintainers

### Code Review Guidelines

- Be respectful and constructive
- Focus on code quality, not personal preferences
- Explain the "why" behind suggestions
- Approve when satisfied, request changes when needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Auth0](https://auth0.com/) - Authentication platform
- [python-jobspy](https://github.com/cullenwatson/JobSpy) - Job scraping library
- [Celery](https://docs.celeryq.dev/) - Distributed task queue

## Support

If you find this project helpful, please consider:
- Starring the repository
- Sharing it with others
- Contributing improvements
- Reporting bugs

