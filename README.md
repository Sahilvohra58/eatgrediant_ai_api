# EatGrediant AI API

A simple FastAPI Hello World application designed for deployment on Google Cloud Run.

## Features

- FastAPI web framework
- Health check endpoint for Cloud Run
- Application info endpoint
- Docker containerized for easy deployment
- Production-ready configuration

## Endpoints

- `GET /` - Hello World message
- `GET /health` - Health check endpoint
- `GET /info` - Application information

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

The app will be available at `http://localhost:8000`

## Docker Deployment

1. Build the Docker image:
```bash
docker build -t eatgrediant-ai-api .
```

2. Run the container:
```bash
docker run -p 8080:8080 eatgrediant-ai-api
```

## Google Cloud Run Deployment

1. Make sure you have the Google Cloud CLI installed and authenticated
2. Set your project ID:
```bash
export PROJECT_ID=your-project-id
```

3. Build and push to Google Container Registry:
```bash
docker build -t gcr.io/$PROJECT_ID/eatgrediant-ai-api .
docker push gcr.io/$PROJECT_ID/eatgrediant-ai-api
```

4. Deploy to Cloud Run:
```bash
gcloud run deploy eatgrediant-ai-api \
  --image gcr.io/$PROJECT_ID/eatgrediant-ai-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

Alternatively, you can use Cloud Build for a more streamlined deployment:

1. Create a `cloudbuild.yaml` file (optional)
2. Deploy directly from source:
```bash
gcloud run deploy eatgrediant-ai-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Requirements

- Python 3.11+
- FastAPI 0.104.1
- Uvicorn 0.24.0
