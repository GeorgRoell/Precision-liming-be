# NextFarming Backend API

Secure backend server for NextFarming liming prescription application.

## Features

- 🔒 **Secure**: API credentials stored server-side only
- 🧮 **VDLUFA & CEC Calculations**: Proprietary liming algorithms protected
- 🔑 **Authentication**: JWT-based user authentication
- 🚀 **Fast**: Built with FastAPI
- ☁️ **Cloud-Ready**: Designed for Google Cloud Run deployment

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your credentials
```

### 3. Run Locally

```bash
python main.py
```

Server will start at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Project Structure

```
nextfarming-backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── Dockerfile              # Docker container definition
├── api/                    # API endpoints
│   ├── auth.py            # Authentication endpoints
│   ├── liming.py          # Liming calculation endpoints
│   └── __init__.py
├── calculators/            # Business logic (protected)
│   ├── liming.py          # VDLUFA & CEC calculations
│   └── __init__.py
├── config/                 # Configuration
│   ├── settings.py        # App settings
│   └── __init__.py
├── models/                 # Data models
│   ├── schemas.py         # Pydantic schemas
│   └── __init__.py
└── services/               # External services
    └── __init__.py
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login (returns JWT token)
- `GET /auth/me` - Get current user info

### Liming Calculations
- `POST /liming/calculate/vdlufa` - VDLUFA method calculation
- `POST /liming/calculate/cec` - CEC method calculation

## Deployment

### Google Cloud Run

```bash
gcloud run deploy nextfarming-api \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

See deployment guide for full instructions.

## Security

- ✅ All credentials stored in environment variables
- ✅ Secrets managed via Google Cloud Secret Manager
- ✅ JWT authentication for all endpoints
- ✅ CORS configured for specific origins
- ✅ HTTPS enforced in production

## Development

```bash
# Run with auto-reload
uvicorn main:app --reload --port 8000

# Run tests
pytest

# Format code
black .

# Lint
flake8
```

## License

Proprietary - Omya Agriculture
