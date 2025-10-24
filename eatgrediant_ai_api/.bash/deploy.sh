#!/bin/bash

# EatGrediant AI API - Google Cloud Run Deployment Script
# This script deploys the FastAPI app with Gemini AI integration to Cloud Run

set -e  # Exit on any error

echo "🚀 Deploying EatGrediant AI API to Google Cloud Run..."
echo "=================================================="

# Configuration
PROJECT_ID="eat-ingredient"
SERVICE_NAME="eatgrediant-ai-api"
REGION="us-central1"
SERVICE_ACCOUNT="eatgrediant-gemini-sa@eat-ingredient.iam.gserviceaccount.com"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI is not installed. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo "❌ Not authenticated with Google Cloud. Please run:"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
echo "🔧 Setting Google Cloud project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Display current configuration
echo ""
echo "📋 Deployment Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Service Name: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Service Account: $SERVICE_ACCOUNT"
echo "   Memory: 2Gi"
echo "   CPU: 1"
echo "   Timeout: 300s"
echo "   Port: 8080"
echo ""

# # Confirm deployment (skip if --yes flag is provided)
# if [[ "$1" != "--yes" && "$1" != "-y" ]]; then
#     read -p "🤔 Do you want to proceed with the deployment? (y/n): " -n 1 -r
#     echo
#     if [[ ! $REPLY =~ ^[Yy]$ ]]; then
#         echo "❌ Deployment cancelled."
#         exit 1
#     fi
# else
#     echo "✅ Auto-confirming deployment (--yes flag provided)"
# fi

# Start deployment
echo "🚀 Starting deployment..."
echo ""

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --service-account $SERVICE_ACCOUNT \
  --port 8080 \
  --timeout 300 \
  --memory 2Gi \
  --cpu 1 \
  --quiet

# Check if deployment was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment completed successfully!"
    echo ""
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    echo "🌐 Service URL: $SERVICE_URL"
    echo ""
    echo "📋 Available Endpoints:"
    echo "   GET  $SERVICE_URL/                    - Hello World message"
    echo "   GET  $SERVICE_URL/health              - Health check endpoint"
    echo "   GET  $SERVICE_URL/info                - Complete API documentation"
    echo "   POST $SERVICE_URL/get-product-name    - Extract product name and brand"
    echo "   POST $SERVICE_URL/get-ingredients     - Extract ingredients list"
    echo "   POST $SERVICE_URL/get-nutrition       - Extract nutritional information"
    echo "   POST $SERVICE_URL/get-weight          - Extract weight/quantity information"
    echo ""
    
    # Test the health endpoint
    echo "🧪 Testing health endpoint..."
    if curl -s -f "$SERVICE_URL/health" > /dev/null; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed. The service might still be starting up."
    fi
    
    echo ""
    echo "🎉 Deployment successful! Your API is now live."
    echo ""
    echo "🧪 Testing Options:"
    echo ""
    echo "📦 Test Product Name Extraction:"
    echo "   python3 test_product_analysis.py --product"
    echo "   curl -X POST -F \"file=@front_image.jpg\" -F \"bar_code=123456789\" $SERVICE_URL/get-product-name"
    echo ""
    echo "🧪 Test Ingredients Extraction:"
    echo "   python3 test_product_analysis.py --ingredients"
    echo "   curl -X POST -F \"file=@ingredients_image.jpg\" -F \"bar_code=123456789\" $SERVICE_URL/get-ingredients"
    echo ""
    echo "🥗 Test Nutrition Analysis:"
    echo "   python3 test_product_analysis.py --nutrition"
    echo "   curl -X POST -F \"file=@nutrition_image.jpg\" -F \"bar_code=123456789\" $SERVICE_URL/get-nutrition"
    echo ""
    echo "⚖️  Test Weight Extraction:"
    echo "   python3 test_product_analysis.py --weight"
    echo "   curl -X POST -F \"file=@weight_image.jpg\" -F \"bar_code=123456789\" $SERVICE_URL/get-weight"
    echo ""
    echo "🔍 Test All Endpoints:"
    echo "   python3 test_product_analysis.py"
    echo ""
    echo "📝 Available Test Images:"
    echo "   • test_data/front_amul_icecream.jpg - Product name testing"
    echo "   • test_data/ingredients_amul_icecream.jpg - Ingredients testing"
    echo "   • test_data/nutrition_amul_icecream.jpg - Nutrition testing"
    echo "   • test_data/front_pringles.jpg - Additional product testing"
    echo ""
    echo "📋 Endpoint Parameters:"
    echo "   All POST endpoints require:"
    echo "   • file: Image file (UploadFile)"
    echo "   • bar_code: String identifier for the product"
    echo ""
    echo "🔗 API Documentation:"
    echo "   Visit $SERVICE_URL/info for complete API documentation"
    
else
    echo ""
    echo "❌ Deployment failed. Please check the error messages above."
    exit 1
fi
