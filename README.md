# EduForge

A multi-tenant EdTech SaaS platform designed for coaching institutes, schools, and educational organizations. EduForge provides a comprehensive suite of tools for managing students, exams, billing, notifications, and AI-powered learning experiences.

---

## Overview

EduForge is a modular, microservices-based platform that enables educational institutions to manage their entire workflow from a single system. Each tenant (institution) operates in complete isolation with dedicated schemas, ensuring data security and customizability.

### Key Features

- **Multi-Tenant Architecture** - Schema-per-tenant isolation within each microservice database schema
- **Identity & Access Management** - Role-based access control (Super Admin, Institute Admin, Teacher, Student, Parent)
- **Portal** - Server-rendered admin and teacher dashboard with real-time interactivity
- **Exam Engine** - Create, schedule, proctor, and auto-grade assessments
- **Notifications** - Multi-channel delivery via WhatsApp, SMS, email, and push notifications
- **Billing** - Razorpay-integrated fee management, invoicing, and payment tracking
- **AI Services** - Question generation, answer evaluation, learning analytics, and doubt resolution
- **Analytics** - Real-time dashboards and reporting for institutional decision-making

---

## Architecture

EduForge follows a **microservices architecture** with 7 independently deployable services communicating over REST APIs and asynchronous message queues.

```
                         +--------------+
                         |   Cloudflare |
                         |   CDN + R2   |
                         +------+-------+
                                |
                         +------+-------+
                         |    Nginx     |
                         |   Gateway    |
                         +------+-------+
                                |
        +-----------+-----------+-----------+-----------+-----------+-----------+
        |           |           |           |           |           |           |
   +----+----+ +----+----+ +----+----+ +----+----+ +----+----+ +----+----+ +----+----+
   |Identity | | Portal  | |  Exam   | | Notify  | | Billing | |   AI    | |Analytics|
   | :8001   | | :8002   | | :8003   | | :8004   | | :8005   | | :8006   | | :8007   |
   | FastAPI | | Django  | | FastAPI | | FastAPI | | FastAPI | | FastAPI | | FastAPI |
   +---------+ +---------+ +---------+ +---------+ +---------+ +---------+ +---------+
        |           |           |           |           |           |           |
        +-----------+-----------+-----------+-----------+-----------+-----------+
                                |                               |
                         +------+-------+              +--------+------+
                         | PostgreSQL 16|              |   LocalStack  |
                         | (7 schemas)  |              |   SQS / S3    |
                         +--------------+              +---------------+
```

### Service Responsibilities

| Service        | Framework | Port | Description                                      |
|----------------|-----------|------|--------------------------------------------------|
| **Identity**   | FastAPI   | 8001 | Authentication, authorization, tenant management  |
| **Portal**     | Django    | 8002 | Admin/teacher dashboard, HTMX-powered UI          |
| **Exam**       | FastAPI   | 8003 | Question banks, test creation, proctoring, grading |
| **Notification** | FastAPI | 8004 | WhatsApp, SMS, email, push notification delivery  |
| **Billing**    | FastAPI   | 8005 | Fee management, Razorpay integration, invoicing   |
| **AI**         | FastAPI   | 8006 | Question generation, answer evaluation, tutoring  |
| **Analytics**  | FastAPI   | 8007 | Dashboards, reports, data aggregation             |

---

## Tech Stack

### Backend
- **FastAPI** - High-performance async APIs (Identity, Exam, Notification, Billing, AI, Analytics)
- **Django + HTMX** - Server-rendered portal with real-time interactivity
- **Python 3.12** - Runtime for all backend services
- **SQLAlchemy / Django ORM** - Database access layer
- **Pydantic v2** - Data validation and serialization
- **Celery** - Distributed task queue for background jobs

### Frontend
- **Django Templates + HTMX + Alpine.js** - Portal web interface
- **Flutter** - Cross-platform mobile application (iOS + Android)

### Database & Storage
- **PostgreSQL 16** - Primary database with schema-per-service isolation
- **Cloudflare R2** - Object storage for files, media, and documents
- **Cloudflare CDN** - Global content delivery and edge caching

### Infrastructure
- **AWS ECS (Fargate)** - Container orchestration for production
- **AWS Lambda** - Serverless functions for event-driven workloads
- **Amazon SQS** - Message queue for async inter-service communication
- **Docker + Docker Compose** - Local development environment
- **Nginx** - API gateway and reverse proxy

### DevOps & Tooling
- **Ruff** - Python linting and formatting
- **pytest** - Testing framework
- **mypy** - Static type checking
- **GitHub Actions** - CI/CD pipelines
- **Alembic** - Database migrations (FastAPI services)
- **Django Migrations** - Database migrations (Portal service)

---

## Project Structure

```
Eduforge/
├── services/
│   ├── identity/          # FastAPI - Auth, users, tenants
│   │   ├── app/
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── portal/            # Django - Admin dashboard
│   │   ├── portal/
│   │   ├── templates/
│   │   ├── static/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── exam/              # FastAPI - Exam engine
│   ├── notification/      # FastAPI - Notifications
│   ├── billing/           # FastAPI - Payments & invoicing
│   ├── ai/                # FastAPI - AI/ML services
│   └── analytics/         # FastAPI - Reporting
├── mobile/
│   └── eduforge_app/      # Flutter mobile application
├── packages/
│   └── shared/            # Shared Python utilities and models
├── infra/
│   ├── terraform/         # Infrastructure as code
│   └── k8s/               # Kubernetes manifests (if applicable)
├── scripts/
│   └── init-db.sql        # Database initialization
├── docker-compose.yml
├── docker-compose.override.yml
├── pyproject.toml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- **Docker** >= 24.0 and **Docker Compose** >= 2.20
- **Python** >= 3.12 (for local development without Docker)
- **Flutter** >= 3.19 (for mobile development)
- **Make** (optional, for Makefile targets)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/eduforge.git
   cd eduforge
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

3. **Start all services**

   ```bash
   make up
   # Or without Make:
   docker compose up -d
   ```

4. **Verify services are running**

   ```bash
   docker compose ps
   ```

   | Service       | URL                        |
   |---------------|----------------------------|
   | Identity API  | http://localhost:8001/docs  |
   | Portal        | http://localhost:8002       |
   | Exam API      | http://localhost:8003/docs  |
   | Notification  | http://localhost:8004/docs  |
   | Billing API   | http://localhost:8005/docs  |
   | AI API        | http://localhost:8006/docs  |
   | Analytics API | http://localhost:8007/docs  |

5. **Run database migrations**

   ```bash
   make migrate
   ```

---

## Development

### Running Individual Services

```bash
# Start only specific services
docker compose up -d postgres identity portal

# View logs for a service
make logs service=identity

# Open a shell inside a service container
make shell-identity
```

### Code Quality

```bash
# Run linter
make lint

# Auto-format code
make format

# Run type checking
mypy services/
```

### Adding a New Migration

For FastAPI services (using Alembic):

```bash
cd services/identity
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```

For the Portal service (using Django):

```bash
cd services/portal
python manage.py makemigrations
python manage.py migrate
```

### Flutter Mobile App

```bash
cd mobile/eduforge_app
flutter pub get
flutter run
```

---

## Testing

### Run All Tests

```bash
make test
```

### Run Tests for a Specific Service

```bash
docker compose exec identity pytest tests/ -v
docker compose exec portal python manage.py test
```

### Test Coverage

```bash
pytest --cov=services --cov-report=html
open htmlcov/index.html
```

---

## Deployment

### Environments

| Environment | Description                          |
|-------------|--------------------------------------|
| `local`     | Docker Compose on developer machine  |
| `staging`   | AWS ECS Fargate - staging cluster    |
| `production`| AWS ECS Fargate - production cluster |

### Production Architecture

- **Compute**: AWS ECS Fargate for containerized services, AWS Lambda for event-driven functions
- **Database**: Amazon RDS PostgreSQL 16 with Multi-AZ deployment
- **Storage**: Cloudflare R2 for object storage with CDN for global delivery
- **Queue**: Amazon SQS for asynchronous message passing
- **CI/CD**: GitHub Actions with environment-based deployment gates

### Deployment Commands

```bash
# Build production images
make build

# Deploy via CI/CD (triggered on merge to main)
git push origin main

# Manual deployment (use with caution)
# See infra/terraform/ for infrastructure provisioning
```

---

## Contributing

1. Create a feature branch from `main`
2. Make your changes and add tests
3. Run `make lint` and `make test` to verify
4. Open a pull request targeting `main`

---

## License

Proprietary - All rights reserved.
