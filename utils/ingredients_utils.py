"""
Ingredients analysis utility functions for the EatGrediant AI API
"""
import os
import base64
import json
import logging
import asyncio
from datetime import datetime
from fastapi import HTTPException
import vertexai.generative_models as genai
from google.cloud import storage
from .app_utils import load_prompt

logger = logging.getLogger(__name__)

async def analyze_ingredients_with_gemini(image_data: bytes, model) -> dict:
    """Analyze ingredient list from product image using Gemini model"""
    if not model:
        raise HTTPException(status_code=503, detail="Gemini AI service is not available.")
    
    try:
        # Convert image to base64 for Gemini
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_part = genai.Part.from_data(image_data, mime_type="image/jpeg")
        
        # Load ingredients prompt from file
        prompt = load_prompt("prompts/get_ingredients_prompt.txt")
        
        # Generate response
        response = model.generate_content([prompt, image_part])
        
        if not response.text:
            raise Exception("Empty response from Gemini")
            
        logger.info(f"Gemini raw response for ingredients: {response.text}")
        
        # Parse JSON response
        try:
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(response_text)
            
            # Validate required fields for ingredients response
            required_fields = ['ingredients', 'allergens', 'confidence', 'error']
            if not all(field in result for field in required_fields):
                raise ValueError("Invalid ingredients response format from Gemini")
            
            # Ensure ingredients is a list
            if not isinstance(result.get('ingredients'), list):
                result['ingredients'] = []
                
            # Ensure allergens is a list
            if not isinstance(result.get('allergens'), list):
                result['allergens'] = []
                
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for ingredients: {str(e)}, Response: {response.text}")
            raise Exception("Invalid JSON response from Gemini AI")
            
    except Exception as e:
        logger.error(f"Gemini ingredients analysis error: {str(e)}")
        return {
            "ingredients": [],
            "allergens": [],
            "confidence": "low",
            "error": f"Ingredients analysis failed: {str(e)}"
        }

async def upload_ingredient_image_to_gcs(image_data: bytes, filename: str, content_type: str = "image/jpeg", 
                                        bar_code: str = None):
    """
    Asynchronously upload ingredient image to Google Cloud Storage bucket.
    If file exists, it will be overwritten.
    
    Args:
        image_data: The image data as bytes
        filename: Original filename of the uploaded image
        content_type: MIME type of the image
        bar_code: Unique barcode identifier for organizing files
    """
    try:
        # Get GCS configuration from environment variables
        bucket_name = os.getenv("GCS_BUCKET_NAME", "eatgrediant-product-images")
        project_id = os.getenv("PROJECT_ID", "eat-ingredient")
        
        # Create filename based on requirements
        file_extension = os.path.splitext(filename)[1] if filename else ".jpg"
        
        # Create GCS path: bar_code/ingredients_{timestamp}.extension
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gcs_filename = f"{bar_code}/ingredients_{timestamp}{file_extension}".lower()
        
        # Run the blocking GCS operations in a thread pool to make it async
        def _upload_to_gcs():
            client = storage.Client(project=project_id)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(gcs_filename)
            
            # Upload the image data with correct content type (this will overwrite if file exists)
            blob.upload_from_string(image_data, content_type=content_type)
            
            return blob.public_url
        
        # Execute the upload in a thread pool to make it non-blocking
        loop = asyncio.get_event_loop()
        public_url = await loop.run_in_executor(None, _upload_to_gcs)
        
        logger.info(f"Successfully uploaded ingredient image to GCS: {gcs_filename}")
        logger.info(f"Public URL: {public_url}")
        
        return {
            "success": True,
            "gcs_path": gcs_filename,
            "public_url": public_url
        }
        
    except Exception as e:
        logger.error(f"Failed to upload ingredient image to GCS: {str(e)}")
        # Don't raise exception - this is fire-and-forget
        return {
            "success": False,
            "error": str(e)
        }
