"""
General utility functions for the EatGrediant AI API
"""
import os
import io
import logging
from PIL import Image
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

def load_prompt(prompt_file: str = "prompts/get_product_name_prompt.txt") -> str:
    """Load prompt from file"""
    try:
        with open(prompt_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_file}")
        # Fallback to default prompt with food validation
        return """
        Analyze this product image and extract the following information:
        1. Product name/title
        2. Brand name
        3. Whether this is a food product or not
        4. Confidence level (high/medium/low)

        IMPORTANT: Only analyze food and beverage products. This includes:
        - Packaged foods, snacks, cereals, canned goods
        - Beverages (sodas, juices, water, alcohol, coffee, tea)
        - Fresh produce, dairy products, frozen foods
        - Supplements and vitamins
        - Pet food
        - Baby food and formula

        Return the response in this exact JSON format:
        {
            "product_name": "exact product name or description",
            "brand": "brand name",
            "is_food_product": true/false,
            "confidence": "high/medium/low",
            "error": null
        }

        If the product is NOT a food/beverage item (like electronics, clothing, household items, cosmetics, etc.), return:
        {
            "product_name": null,
            "brand": null,
            "is_food_product": false,
            "confidence": "high",
            "error": "This product is not a food or beverage item. Please upload an image of a food product."
        }

        If the image doesn't clearly show a product with readable text or packaging, return:
        {
            "product_name": null,
            "brand": null,
            "is_food_product": null,
            "confidence": "low",
            "error": "Unable to identify product from image. Please upload a clearer image of the product packaging or label."
        }

        Only return the JSON response, nothing else.
        """

async def validate_image(file: UploadFile) -> bytes:
    """Validate uploaded image file"""
    # Check file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    # Check content type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image.")
    
    # Read and validate image
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Check image dimensions (minimum size)
        if image.width < 100 or image.height < 100:
            raise HTTPException(status_code=400, detail="Image too small. Minimum size is 100x100 pixels.")
            
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return contents
    except Exception as e:
        logger.error(f"Image validation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid image file or corrupted image.")
