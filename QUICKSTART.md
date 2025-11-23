# Quick Start Guide

## Step 1: Install Dependencies

```bash
cd nextfarming-backend
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Mac/Linux

pip install -r requirements.txt
```

## Step 2: Configure Environment

The `.env` file has been created with your NextFarming credentials.

**Important**: Never commit `.env` to git!

## Step 3: Run the Server

```bash
python main.py
```

Server will start at: `http://localhost:8000`

## Step 4: Test the API

### Option 1: Open Swagger UI
Visit: `http://localhost:8000/docs`

This gives you an interactive API documentation where you can test endpoints.

### Option 2: Test with curl

**1. Login to get token:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**2. Test liming calculation:**
```bash
curl -X POST "http://localhost:8000/liming/calculate/vdlufa" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "soil_data": [{
      "ph_value": 5.2,
      "soil_texture": "sandy loam",
      "area": 10.5,
      "field_name": "Test Field"
    }],
    "crop_type": "Standard crops",
    "lime_type": "CaCO3"
  }'
```

## Step 5: Check Project Structure

```
nextfarming-backend/
├── main.py                 ✅ Created - FastAPI app
├── requirements.txt        ✅ Created - Dependencies
├── .env                    ✅ Created - Configuration
├── Dockerfile              ✅ Created - For deployment
├── api/
│   ├── auth.py            ✅ Created - Authentication
│   └── liming.py          ✅ Created - Liming calculations
├── calculators/
│   └── liming.py          ✅ Copied - Your algorithms (protected!)
├── config/
│   └── settings.py        ✅ Created - App settings
└── models/
    └── schemas.py         ✅ Created - Data models
```

## Default Users

- **Username**: `demo` / **Password**: `demo123`
- **Username**: `admin` / **Password**: `admin123`

## Next Steps

1. ✅ Test locally (you are here!)
2. ⏳ Deploy to Google Cloud Run
3. ⏳ Build web frontend
4. ⏳ Connect desktop app to backend

## Troubleshooting

### Port already in use
```bash
# Change port in main.py or:
python -c "from main import app; import uvicorn; uvicorn.run(app, port=8001)"
```

### Module not found
```bash
# Make sure virtual environment is activated
pip install -r requirements.txt
```

### Import errors
```bash
# Check you're in the right directory
cd nextfarming-backend
python main.py
```
