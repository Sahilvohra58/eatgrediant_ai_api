# EatGrediant AI API

A FastAPI application with Gemini AI product analysis capabilities designed for deployment on Google Cloud Run.

## Features

- FastAPI web framework
- Gemini AI integration for product analysis
- Image processing and analysis
- Google Cloud Storage integration
- Health check endpoint for Cloud Run
- Comprehensive API documentation
- Docker containerized for easy deployment
- Production-ready configuration

## Endpoints

### GET Endpoints
- `GET /` - Hello World message
- `GET /health` - Health check endpoint for Cloud Run
- `GET /info` - Complete API information and endpoint documentation

### POST Endpoints (Image Analysis)
- `POST /get-product-name` - Extract product name and brand from food product image
  - Parameters: `file` (UploadFile), `bar_code` (str)
  - Returns: Product name, brand, confidence level
  
- `POST /get-ingredients` - Extract ingredients list from product image
  - Parameters: `file` (UploadFile), `bar_code` (str)
  - Returns: Ingredients list, allergens, confidence level
  
- `POST /get-nutrition` - Extract nutritional information from nutrition label
  - Parameters: `file` (UploadFile), `bar_code` (str)
  - Returns: Nutrition facts, additional nutrients, allergens, dietary claims
  
- `POST /get-weight` - Extract weight/quantity information from product image
  - Parameters: `file` (UploadFile), `bar_code` (str)
  - Returns: Net weight, package count, serving info, weight unit

### Common Features
- All POST endpoints accept image files and automatically upload to Google Cloud Storage
- Asynchronous image analysis with immediate response
- Comprehensive error handling with detailed error messages
- Image validation and content type checking
- Detailed logging for debugging and monitoring

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
