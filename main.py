from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import uvicorn
import os
import asyncio
import vertexai
import vertexai.generative_models as genai
import logging
from utils import validate_image, analyze_product_with_gemini, upload_image_to_gcs, analyze_ingredients_with_gemini, upload_ingredient_image_to_gcs, analyze_nutrition_with_gemini, upload_nutrition_image_to_gcs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
PROJECT_ID = "eat-ingredient"
REGION = "us-central1"

try:
    vertexai.init(project=PROJECT_ID, location=REGION)
    # Try latest Gemini models from official documentation that support image processing
    models_to_try = [
        "gemini-2.5-flash",           # Best price-performance, supports images
        "gemini-2.5-pro",             # State-of-the-art model, supports images  
        "gemini-2.0-flash",           # Second generation workhorse, supports images
        "gemini-2.0-flash-lite",      # Cost efficient, supports images
        "gemini-2.5-flash-preview-09-2025"  # Preview version
    ]
    
    model = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            logger.info(f"Successfully initialized Vertex AI with model: {model_name}")
            break
        except Exception as model_error:
            logger.warning(f"Failed to initialize model {model_name}: {str(model_error)}")
            continue
    
    if not model:
        raise Exception("No available Gemini models found")
        
except Exception as e:
    logger.error(f"Failed to initialize Vertex AI: {str(e)}")
    model = None

# Create FastAPI app instance
app = FastAPI(title="EatGrediant AI API", version="2.0.0")

@app.get("/")
async def hello_world():
    """Hello World endpoint"""
    return {"message": "Hello World from EatGrediant AI API!"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "message": "API is running successfully"}

@app.get("/info")
async def app_info():
    """Return application information"""
    return {
        "app_name": "EatGrediant AI API",
        "version": "2.0.0",
        "description": "FastAPI application with Gemini AI product analysis deployed on Google Cloud Run",
        "endpoints": {
            "/": "Hello World",
            "/health": "Health check",
            "/info": "API information",
            "/get-product-name": "Get product name and brand from FOOD product image with barcode (POST)",
            "/get-ingredients": "Extract ingredients list from product image with barcode (POST)",
            "/get-nutrition": "Extract nutritional information from product nutrition label with barcode (POST)"
        }
    }



@app.post("/get-product-name")
async def get_product_name(
    file: UploadFile = File(...),
    bar_code: str = Form(...)
):
    """
    Get product name and brand from a FOOD product image using Gemini AI
    
    IMPORTANT: Only accepts food and beverage products including:
    - Packaged foods, snacks, cereals, canned goods
    - Beverages (sodas, juices, water, alcohol, coffee, tea)  
    - Fresh produce, dairy products, frozen foods
    - Supplements and vitamins, pet food, baby food
    
    Upload an image of a food product and get:
    - Product name
    - Brand name  
    - Confidence level
    - Error message if analysis fails or product is not food-related
    
    Parameters:
    - file: Food product image file
    - bar_code: Unique barcode identifier for the product
    
    Returns 400 error if the product is not food/beverage related.
    
    After successful analysis, the image is asynchronously uploaded to GCS bucket
    organized by bar_code folder with filename: front_{product_name}.{extension}
    """
    try:
        logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}, Bar Code: {bar_code}")
        
        # Store file information for later GCS upload
        original_filename = file.filename
        original_content_type = file.content_type
        
        # Validate the uploaded image
        image_data = await validate_image(file)
        
        # Analyze with Gemini
        result = await analyze_product_with_gemini(image_data, model)
        
        # Check if analysis was successful
        if result.get("error"):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result["error"],
                    "data": None
                }
            )
        
        # Create background task for GCS upload (fire-and-forget)
        # This runs asynchronously after the response is returned
        asyncio.create_task(
            upload_image_to_gcs(
                image_data=image_data,
                filename=original_filename or "unknown.jpg",
                content_type=original_content_type or "image/jpeg",
                bar_code=bar_code,
                product_name=result["product_name"] or "unknown_product",
                product_brand=result["brand"] or "unknown_brand"
            )
        )
        
        logger.info(f"Started background GCS upload task for file: {original_filename}")
        
        # Return successful analysis immediately
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Product analysis completed successfully",
                "data": {
                    "product_name": result["product_name"],
                    "brand": result["brand"],
                    "confidence": result["confidence"]
                }
            }
        )
        
    except HTTPException as e:
        logger.error(f"HTTP Exception: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/get-ingredients")
async def get_ingredients(
    file: UploadFile = File(...),
    bar_code: str = Form(...)
):
    """
    Extract ingredients list from product image using Gemini AI
    
    This endpoint analyzes the ingredients list from the back or side of product packaging.
    Upload an image showing the ingredients section and get a complete list of all ingredients.
    
    Parameters:
    - file: Product image file showing ingredients list
    - bar_code: Unique barcode identifier for the product
    
    Returns:
    - List of all ingredients extracted from the image
    - Total count of ingredients found
    - Confidence level of the extraction
    - Error message if analysis fails
    
    After successful analysis, the image is asynchronously uploaded to GCS bucket
    organized by bar_code folder with filename: ingredients_{timestamp}.{extension}
    """
    try:
        logger.info(f"Received ingredients file: {file.filename}, Content-Type: {file.content_type}, Bar Code: {bar_code}")
        
        # Store file information for later GCS upload
        original_filename = file.filename
        original_content_type = file.content_type
        
        # Validate the uploaded image
        image_data = await validate_image(file)
        
        # Analyze ingredients with Gemini
        result = await analyze_ingredients_with_gemini(image_data, model)
        
        # Check if analysis was successful
        if result.get("error"):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result["error"],
                    "data": None
                }
            )
        
        # Create background task for GCS upload (fire-and-forget)
        # This runs asynchronously after the response is returned
        asyncio.create_task(
            upload_ingredient_image_to_gcs(
                image_data=image_data,
                filename=original_filename or "unknown.jpg",
                content_type=original_content_type or "image/jpeg",
                bar_code=bar_code
            )
        )
        
        logger.info(f"Started background GCS upload task for ingredients file: {original_filename}")
        
        # Return successful analysis immediately
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Ingredients extraction completed successfully",
                "data": {
                    "ingredients": result["ingredients"],
                    "allergens": result["allergens"],
                    "confidence": result["confidence"]
                }
            }
        )
        
    except HTTPException as e:
        logger.error(f"HTTP Exception in get_ingredients: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in get_ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/get-nutrition")
async def get_nutrition(
    file: UploadFile = File(...),
    bar_code: str = Form(...)
):
    """
    Extract nutritional information from product nutrition label using Gemini AI
    
    This endpoint analyzes the nutrition facts panel and any additional nutritional information
    visible on product packaging. Upload an image showing the nutrition label and get complete
    nutritional data including macronutrients, micronutrients, allergens, and dietary claims.
    
    Parameters:
    - file: Product image file showing nutrition facts label
    - bar_code: Unique barcode identifier for the product
    
    Returns:
    - Complete nutrition facts including calories, fats, carbohydrates, proteins, vitamins, minerals
    - Additional nutrients like vitamins and minerals if visible
    - Allergen information found on packaging
    - Dietary claims (organic, gluten-free, vegan, etc.)
    - Confidence level of the extraction
    - Error message if analysis fails
    
    After successful analysis, the image is asynchronously uploaded to GCS bucket
    organized by bar_code folder with filename: nutrition_{timestamp}.{extension}
    """
    try:
        logger.info(f"Received nutrition file: {file.filename}, Content-Type: {file.content_type}, Bar Code: {bar_code}")
        
        # Store file information for later GCS upload
        original_filename = file.filename
        original_content_type = file.content_type
        
        # Validate the uploaded image
        image_data = await validate_image(file)
        
        # Analyze nutrition with Gemini
        result = await analyze_nutrition_with_gemini(image_data, model)
        
        # Check if analysis was successful
        if result.get("error"):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": result["error"],
                    "data": None
                }
            )
        
        # Create background task for GCS upload (fire-and-forget)
        # This runs asynchronously after the response is returned
        asyncio.create_task(
            upload_nutrition_image_to_gcs(
                image_data=image_data,
                filename=original_filename or "unknown.jpg",
                content_type=original_content_type or "image/jpeg",
                bar_code=bar_code
            )
        )
        
        logger.info(f"Started background GCS upload task for nutrition file: {original_filename}")
        
        # Return successful analysis immediately
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Nutrition analysis completed successfully",
                "data": {
                    "nutrition_facts": result["nutrition_facts"],
                    "additional_nutrients": result["additional_nutrients"],
                    "allergens": result["allergens"],
                    "dietary_claims": result["dietary_claims"],
                    "confidence": result["confidence"]
                }
            }
        )
        
    except HTTPException as e:
        logger.error(f"HTTP Exception in get_nutrition: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in get_nutrition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    # Get port from environment variable (Cloud Run sets this)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
