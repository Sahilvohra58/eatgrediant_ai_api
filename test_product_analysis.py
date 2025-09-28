#!/usr/bin/env python3
"""
Test script for the EatGrediant AI API endpoints

Usage:
  python test_product_analysis.py --product          # Test product name endpoint with default image
  python test_product_analysis.py --ingredients      # Test ingredients endpoint with default image
  python test_product_analysis.py --nutrition        # Test nutrition endpoint with default image
  python test_product_analysis.py <image_path>       # Test product name endpoint with custom image
  python test_product_analysis.py --help             # Show help message
"""

import requests
import sys
import json
from pathlib import Path

API_URL = "https://eatgrediant-ai-api-tc5cvwjylq-uc.a.run.app"

def load_test_config():
    """Load test configuration including barcode from input.json"""
    try:
        config_path = Path(__file__).parent / "test_data" / "input.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  Warning: test_data/input.json not found, using default barcode")
        return {"bar_code": "00000000000000"}
    except Exception as e:
        print(f"⚠️  Warning: Error loading config: {str(e)}, using default barcode")
        return {"bar_code": "00000000000000"}

def save_test_results(config, result_type=None, brand=None, product_name=None, ingredients=None, nutrition_facts=None, allergens=None, dietary_claims=None):
    """Save API analysis results back to input.json as separate dictionaries"""
    try:
        config_path = Path(__file__).parent / "test_data" / "input.json"
        
        # Initialize structured sections if they don't exist
        if "product_analysis" not in config:
            config["product_analysis"] = {}
        if "ingredients_analysis" not in config:
            config["ingredients_analysis"] = {}
        if "nutrition_analysis" not in config:
            config["nutrition_analysis"] = {}
        
        # Update appropriate section based on result type
        if result_type == "product" and (brand is not None or product_name is not None):
            if brand is not None:
                config["product_analysis"]["brand"] = brand
            if product_name is not None:
                config["product_analysis"]["product_name"] = product_name
                
        elif result_type == "ingredients" and ingredients is not None:
            config["ingredients_analysis"]["ingredients"] = ingredients
            if allergens is not None:
                config["ingredients_analysis"]["allergens"] = allergens

                
        elif result_type == "nutrition" and nutrition_facts is not None:
            config["nutrition_analysis"]["nutrition_facts"] = nutrition_facts
            if allergens is not None:
                config["nutrition_analysis"]["allergens"] = allergens
            if dietary_claims is not None:
                config["nutrition_analysis"]["dietary_claims"] = dietary_claims
        
        # Clean up old format fields if they exist
        old_fields = ["brand", "product_name", "ingredients", "nutrition_facts", "allergens", "dietary_claims"]
        for field in old_fields:
            if field in config and field != "bar_code":
                # Only remove if the data has been moved to the new structure
                if ((field in ["brand", "product_name"] and config["product_analysis"]) or
                    (field == "ingredients" and config["ingredients_analysis"]) or
                    (field in ["nutrition_facts", "allergens", "dietary_claims"] and config["nutrition_analysis"])):
                    del config[field]
        
        # Write back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 Updated input.json with {result_type} analysis results:")
        
        # Display what was saved
        if result_type == "product":
            if brand is not None:
                print(f"   Brand: {brand}")
            if product_name is not None:
                print(f"   Product: {product_name}")
        elif result_type == "ingredients" and ingredients is not None:
            print(f"   Ingredients: {len(ingredients)} items")
            print(f"   First 5 ingredients: {', '.join(ingredients[:5])}{'...' if len(ingredients) > 5 else ''}")
            if allergens is not None and len(allergens) > 0:
                print(f"   Allergens: {', '.join(allergens)}")
        elif result_type == "nutrition" and nutrition_facts is not None:
            # Handle value/unit structure or fallback to old format
            calories = nutrition_facts.get('calories', 'N/A')
            if isinstance(calories, dict):
                calories_str = f"{calories.get('value', 'N/A')} {calories.get('unit', '')}" if calories.get('value') else 'N/A'
            else:
                calories_str = str(calories)
                
            serving_size = nutrition_facts.get('serving_size', 'N/A')
            amount_per = nutrition_facts.get('amount_per', 'N/A')
            print(f"   Nutrition: {calories_str} {amount_per} (serving size: {serving_size})")
            if allergens is not None and len(allergens) > 0:
                print(f"   Allergens: {', '.join(allergens)}")
            if dietary_claims is not None and len(dietary_claims) > 0:
                print(f"   Dietary Claims: {', '.join(dietary_claims)}")
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to save results to input.json: {str(e)}")

def test_product_analysis(image_path):
    """Test the product analysis endpoint with an image file"""
    
    # Check if file exists
    if not Path(image_path).exists():
        print(f"❌ Error: Image file '{image_path}' not found")
        return
    
    # Load test configuration
    config = load_test_config()
    bar_code = config.get("bar_code", "00000000000000")
    
    # Prepare the file for upload
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/jpeg')}
            data = {'bar_code': bar_code}
            
            print(f"🔄 Analyzing product image: {image_path}")
            print(f"🏷️  Using barcode: {bar_code}")
            print(f"📡 Sending request to: {API_URL}/get-product-name")
            
            # Send POST request to get-product-name endpoint
            response = requests.post(
                f"{API_URL}/get-product-name",
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            # Parse and display the response
            if response.status_code == 200:
                result = response.json()
                print("✅ Analysis completed successfully!")
                print(json.dumps(result, indent=2))
                
                if result.get('success'):
                    data = result.get('data', {})
                    product_name = data.get('product_name', 'N/A')
                    brand = data.get('brand', 'N/A')
                    confidence = data.get('confidence', 'N/A')
                    
                    print(f"\n🏷️  Product: {product_name}")
                    print(f"🏢 Brand: {brand}")
                    print(f"🎯 Confidence: {confidence}")
                    
                    # Save results back to input.json if analysis was successful
                    if product_name != 'N/A' and brand != 'N/A':
                        save_test_results(config, result_type="product", brand=brand, product_name=product_name)
                    
            else:
                print(f"❌ Request failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text)
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_ingredients_analysis(image_path):
    """Test the ingredients analysis endpoint with an image file"""
    
    # Check if file exists
    if not Path(image_path).exists():
        print(f"❌ Error: Image file '{image_path}' not found")
        return
    
    # Load test configuration
    config = load_test_config()
    bar_code = config.get("bar_code", "00000000000000")
    
    # Prepare the file for upload
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/jpeg')}
            data = {'bar_code': bar_code}
            
            print(f"🔄 Analyzing ingredients image: {image_path}")
            print(f"🏷️  Using barcode: {bar_code}")
            print(f"📡 Sending request to: {API_URL}/get-ingredients")
            
            # Send POST request to get-ingredients endpoint
            response = requests.post(
                f"{API_URL}/get-ingredients",
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            # Parse and display the response
            if response.status_code == 200:
                result = response.json()
                print("✅ Ingredients analysis completed successfully!")
                print(json.dumps(result, indent=2))
                
                if result.get('success'):
                    data = result.get('data', {})
                    ingredients = data.get('ingredients', [])
                    allergens = data.get('allergens', [])
                    confidence = data.get('confidence', 'N/A')
                    
                    print(f"\n🧪 Ingredients Found: {len(ingredients)}")
                    print(f"🎯 Confidence: {confidence}")
                    print(f"📝 Ingredients List:")
                    for i, ingredient in enumerate(ingredients, 1):
                        print(f"   {i}. {ingredient}")
                    
                    # Display allergens if found
                    if allergens and len(allergens) > 0:
                        print(f"\n⚠️  Allergens Found: {', '.join(allergens)}")
                    
                    # Save ingredients results to input.json if analysis was successful
                    if ingredients and len(ingredients) > 0:
                        save_test_results(config, result_type="ingredients", ingredients=ingredients, allergens=allergens)
                    
            else:
                print(f"❌ Request failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text)
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_nutrition_analysis(image_path):
    """Test the nutrition analysis endpoint with an image file"""
    
    # Check if file exists
    if not Path(image_path).exists():
        print(f"❌ Error: Image file '{image_path}' not found")
        return
    
    # Load test configuration
    config = load_test_config()
    bar_code = config.get("bar_code", "00000000000000")
    
    # Prepare the file for upload
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/jpeg')}
            data = {'bar_code': bar_code}
            
            print(f"🔄 Analyzing nutrition image: {image_path}")
            print(f"🏷️  Using barcode: {bar_code}")
            print(f"📡 Sending request to: {API_URL}/get-nutrition")
            
            # Send POST request to get-nutrition endpoint
            response = requests.post(
                f"{API_URL}/get-nutrition",
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            # Parse and display the response
            if response.status_code == 200:
                result = response.json()
                print("✅ Nutrition analysis completed successfully!")
                print(json.dumps(result, indent=2))
                
                if result.get('success'):
                    data = result.get('data', {})
                    nutrition_facts = data.get('nutrition_facts', {})
                    additional_nutrients = data.get('additional_nutrients', {})
                    allergens = data.get('allergens', [])
                    dietary_claims = data.get('dietary_claims', [])
                    confidence = data.get('confidence', 'N/A')
                    
                    print(f"\n🥗 Nutrition Analysis Results:")
                    print(f"🎯 Confidence: {confidence}")
                    
                    # Display basic nutrition facts
                    if nutrition_facts:
                        serving_size = nutrition_facts.get('serving_size', 'N/A')
                        amount_per = nutrition_facts.get('amount_per', 'N/A')
                        
                        # Handle value/unit structure or fallback to old format
                        calories = nutrition_facts.get('calories', 'N/A')
                        if isinstance(calories, dict):
                            calories_str = f"{calories.get('value', 'N/A')} {calories.get('unit', '')}" if calories.get('value') else 'N/A'
                        else:
                            calories_str = str(calories)
                            
                        protein = nutrition_facts.get('protein', 'N/A')
                        if isinstance(protein, dict):
                            protein_str = f"{protein.get('value', 'N/A')}{protein.get('unit', '')}" if protein.get('value') else 'N/A'
                        else:
                            protein_str = f"{protein}g" if protein != 'N/A' else 'N/A'
                            
                        total_fat = nutrition_facts.get('total_fat', 'N/A')
                        if isinstance(total_fat, dict):
                            fat_str = f"{total_fat.get('value', 'N/A')}{total_fat.get('unit', '')}" if total_fat.get('value') else 'N/A'
                        else:
                            fat_str = f"{total_fat}g" if total_fat != 'N/A' else 'N/A'
                            
                        total_carbs = nutrition_facts.get('total_carbohydrates', 'N/A')
                        if isinstance(total_carbs, dict):
                            carbs_str = f"{total_carbs.get('value', 'N/A')}{total_carbs.get('unit', '')}" if total_carbs.get('value') else 'N/A'
                        else:
                            carbs_str = f"{total_carbs}g" if total_carbs != 'N/A' else 'N/A'
                        
                        print(f"\n📏 Serving Size: {serving_size}")
                        print(f"📊 Amount Per: {amount_per}")
                        print(f"⚡ Calories: {calories_str}")
                        print(f"🥩 Protein: {protein_str}")
                        print(f"🧈 Total Fat: {fat_str}")
                        print(f"🍞 Total Carbohydrates: {carbs_str}")
                    
                    # Display allergens
                    if allergens and len(allergens) > 0:
                        print(f"\n⚠️  Allergens: {', '.join(allergens)}")
                    
                    # Display dietary claims
                    if dietary_claims and len(dietary_claims) > 0:
                        print(f"\n🌱 Dietary Claims: {', '.join(dietary_claims)}")
                    
                    # Save nutrition results to input.json if analysis was successful
                    if nutrition_facts:
                        save_test_results(config, 
                                        result_type="nutrition",
                                        nutrition_facts=nutrition_facts,
                                        allergens=allergens if allergens else None,
                                        dietary_claims=dietary_claims if dietary_claims else None)
                    
            else:
                print(f"❌ Request failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text)
                    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_all_endpoints():
    """Test all available endpoints"""
    
    endpoints = [
        ("Root", "/"),
        ("Health Check", "/health"),
        ("API Info", "/info")
    ]
    
    print("🧪 Testing all endpoints...\n")
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{API_URL}{endpoint}", timeout=10)
            print(f"✅ {name} ({endpoint}): {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if endpoint == "/info":
                    print(f"   Available endpoints: {list(result.get('endpoints', {}).keys())}")
        except Exception as e:
            print(f"❌ {name} ({endpoint}): Failed - {str(e)}")
    
    print()

def test_product_with_default_image():
    """Test product name endpoint with default Amul ice cream image"""
    script_dir = Path(__file__).parent
    product_image = script_dir / "test_data" / "front_amul_icecream.jpg"
    
    print("📦 Testing Product Name Extraction with default image")
    print("-" * 50)
    
    if product_image.exists():
        test_product_analysis(str(product_image))
    else:
        print(f"❌ Test image not found: {product_image}")

def test_ingredients_with_default_image():
    """Test ingredients endpoint with default Amul ice cream ingredients image"""
    script_dir = Path(__file__).parent
    ingredients_image = script_dir / "test_data" / "ingredients_amul_icecream.jpg"
    
    print("🧪 Testing Ingredients Extraction with default image")
    print("-" * 50)
    
    if ingredients_image.exists():
        test_ingredients_analysis(str(ingredients_image))
    else:
        print(f"❌ Test image not found: {ingredients_image}")

def test_nutrition_with_default_image():
    """Test nutrition endpoint with default Amul ice cream nutrition image"""
    script_dir = Path(__file__).parent
    nutrition_image = script_dir / "test_data" / "nutrition_amul_icecream.jpg"
    
    print("🥗 Testing Nutrition Extraction with default image")
    print("-" * 50)
    
    if nutrition_image.exists():
        test_nutrition_analysis(str(nutrition_image))
    else:
        print(f"❌ Test image not found: {nutrition_image}")

if __name__ == "__main__":
    print("🚀 EatGrediant AI API - Product Analysis Test")
    print("=" * 50)
    
    # Test basic endpoints first
    test_all_endpoints()
    
    # Handle different command line arguments
    if len(sys.argv) == 1:
        # No arguments - test all endpoints with default images
        print("\n🧪 Testing All Endpoints with Default Images")
        print("=" * 60)
        
        # Test product name endpoint
        print("\n📦 Testing Product Name Endpoint")
        test_product_with_default_image()
        
        print("\n" + "=" * 60)
        
        # Test ingredients endpoint  
        print("\n🧪 Testing Ingredients Endpoint")
        test_ingredients_with_default_image()
        
        print("\n" + "=" * 60)
        
        # Test nutrition endpoint
        print("\n🥗 Testing Nutrition Endpoint")
        test_nutrition_with_default_image()
        
        print("\n" + "=" * 60)
        print("✅ All endpoint testing completed!")
        
        print("\n📝 Individual Usage Options:")
        print("  python test_product_analysis.py --product          # Test product name only")
        print("  python test_product_analysis.py --ingredients      # Test ingredients only")
        print("  python test_product_analysis.py --nutrition        # Test nutrition only")
        print("  python test_product_analysis.py <image_path>       # Test product name with custom image")
        
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        
        if arg == "--ingredients":
            # Test ingredients endpoint with default image
            test_ingredients_with_default_image()
                
        elif arg == "--product":
            # Test product name endpoint with default image
            test_product_with_default_image()
            
        elif arg == "--nutrition":
            # Test nutrition endpoint with default image
            test_nutrition_with_default_image()
            
        elif arg == "--help" or arg == "-h":
            # Show help
            print("\n📝 Usage:")
            print("  python test_product_analysis.py --product          # Test product name with default image")
            print("  python test_product_analysis.py --ingredients      # Test ingredients with default image")
            print("  python test_product_analysis.py --nutrition        # Test nutrition with default image")
            print("  python test_product_analysis.py <image_path>       # Test product name with custom image")
            print("  python test_product_analysis.py --help             # Show this help message")
            print("\nDefault Test Images:")
            print("  🏷️  Product Name: test_data/front_amul_icecream.jpg")
            print("  🧪 Ingredients: test_data/ingredients_amul_icecream.jpg")
            print("  🥗 Nutrition: test_data/nutrition_amul_icecream.jpg")
            print("\n🔍 Images should show clear, readable text for best results")
            print("\nEndpoints:")
            print("  📦 Product Name: /get-product-name")
            print("  🧪 Ingredients: /get-ingredients")
            print("  🥗 Nutrition: /get-nutrition")
            
        else:
            # Single argument - treat as product image path for product name testing
            print("📦 Testing Product Name Extraction with custom image")
            print("-" * 50)
            test_product_analysis(arg)
            
    else:
        print("❌ Too many arguments provided.")
        print("📝 Usage: python test_product_analysis.py --help for options")
