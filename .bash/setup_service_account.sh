#!/bin/bash

# EatGrediant AI API - Service Account Setup Script
# This script creates a service account with appropriate permissions for:
# - Vertex AI (Gemini)
# - BigQuery
# - Cloud Storage (GCS)
# - Firestore

set -e  # Exit on any error

echo "🔧 Setting up Service Account for EatGrediant AI API..."
echo "================================================="

# Configuration
PROJECT_ID="eat-ingredient"
SA_NAME="eatgrediant-cloud-functions-sa"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
SA_DISPLAY_NAME="EatGrediant Cloud Functions Service Account"
SA_DESCRIPTION="Service account for EatGrediant AI API with access to Vertex AI, BigQuery, GCS, and Firestore"

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

echo ""
echo "📋 Service Account Configuration:"
echo "   Name: $SA_NAME"
echo "   Email: $SA_EMAIL"
echo "   Display Name: $SA_DISPLAY_NAME"
echo ""

# Check if service account already exists
if gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
    echo "⚠️  Service account already exists: $SA_EMAIL"
    read -p "🤔 Do you want to update the existing service account permissions? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 1
    fi
    SKIP_CREATION=true
else
    SKIP_CREATION=false
fi

# Create service account if it doesn't exist
if [ "$SKIP_CREATION" = false ]; then
    echo "🛠️  Creating service account..."
    gcloud iam service-accounts create $SA_NAME \
        --display-name="$SA_DISPLAY_NAME" \
        --description="$SA_DESCRIPTION"
    echo "✅ Service account created successfully!"
fi

echo ""
echo "🔐 Assigning IAM roles..."

# Define the roles needed for each service
declare -a ROLES=(
    # Vertex AI roles for Gemini
    "roles/aiplatform.user"
    "roles/ml.developer"
    
    # BigQuery roles
    # "roles/bigquery.dataEditor"
    # "roles/bigquery.jobUser"
    # "roles/bigquery.dataViewer"
    
    # Cloud Storage roles
    "roles/storage.objectAdmin"
    "roles/storage.legacyBucketReader"
    
    # Firestore roles
    "roles/datastore.user"
    "roles/firebase.developAdmin"
    
    # Basic service account roles
    "roles/serviceusage.serviceUsageConsumer"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
)

# Assign each role
for role in "${ROLES[@]}"; do
    echo "   Adding role: $role"
    if gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --quiet; then
        echo "   ✅ Successfully added $role"
    else
        echo "   ❌ Failed to add $role"
    fi
done

echo ""
echo "🔑 Creating service account key..."
KEY_FILE="$SA_NAME-key.json"

# Remove existing key file if it exists
if [ -f "$KEY_FILE" ]; then
    rm "$KEY_FILE"
fi

# Create new key
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL"

echo "✅ Service account key created: $KEY_FILE"

echo ""
echo "🚨 IMPORTANT SECURITY NOTES:"
echo "   1. Keep the key file ($KEY_FILE) secure and never commit it to version control"
echo "   2. Consider using Workload Identity instead of key files in production"
echo "   3. Regularly rotate service account keys"
echo "   4. Add $KEY_FILE to your .gitignore file"

echo ""
echo "📝 Next Steps:"
echo "   1. Add the key file to your environment:"
echo "      export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/$KEY_FILE\""
echo ""
echo "   2. For Cloud Run deployment, the service account will be used automatically"
echo ""
echo "   3. Test the permissions with your application"
echo ""

echo "✅ Service account setup completed successfully!"
echo ""
echo "🔍 Service Account Details:"
echo "   Email: $SA_EMAIL"
echo "   Roles assigned: ${#ROLES[@]} roles"
echo "   Key file: $KEY_FILE"
