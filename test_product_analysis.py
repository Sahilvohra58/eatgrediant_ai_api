#!/usr/bin/env python3
"""
Test script for the EatGrediant AI API endpoints

Usage:
  # Default: test on cloud deployment
  python3 test_product_analysis.py --product          # Test product name endpoint with default image
  python3 test_product_analysis.py --ingredients      # Test ingredients endpoint with default image
  python3 test_product_analysis.py --nutrition        # Test nutrition endpoint with default image
  python3 test_product_analysis.py --weight           # Test weight endpoint with default image
  python3 test_product_analysis.py <image_path>       # Test product name endpoint with custom image
  
  # Force specific environment
  python3 test_product_analysis.py --local --product  # Test locally
  python3 test_product_analysis.py --cloud --product  # Test on Cloud Run (explicit)
  python3 test_product_analysis.py --auto --product   # Auto-detect (try local first, then cloud)
  
  # Other options
  python3 test_product_analysis.py --help             # Show help message
  python3 test_product_analysis.py --status           # Show environment status
"""

import requests
import sys
import json
import os
import argparse
from pathlib import Path

# Default URLs
LOCAL_API_URL = "http://localhost:8000"
CLOUD_API_URL = "https://eatgrediant-ai-api-612068620881.us-central1.run.app"

# Allow override via environment variables
LOCAL_API_URL = os.getenv("LOCAL_API_URL", LOCAL_API_URL)
CLOUD_API_URL = os.getenv("CLOUD_API_URL", CLOUD_API_URL)

# Global variable to hold the selected API URL
API_URL = None

def check_local_server_status():
    """Check if local server is running and accessible"""
    try:
        response = requests.get(f"{LOCAL_API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def check_cloud_server_status():
    """Check if cloud server is accessible"""
    try:
        response = requests.get(f"{CLOUD_API_URL}/health", timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def select_api_url(force_local=False, force_cloud=False, auto_detect=False):
    """Select the appropriate API URL based on availability and user preference"""
    global API_URL
    
    if force_local:
        if check_local_server_status():
            API_URL = LOCAL_API_URL
            print(f"🏠 Using LOCAL environment: {API_URL}")
            return True
        else:
            print(f"❌ Local server not accessible at {LOCAL_API_URL}")
            print("💡 Make sure the local server is running with: poetry run python main.py")
            return False
    
    elif force_cloud:
        if check_cloud_server_status():
            API_URL = CLOUD_API_URL
            print(f"☁️  Using CLOUD environment: {API_URL}")
            return True
        else:
            print(f"❌ Cloud server not accessible at {CLOUD_API_URL}")
            return False
    
    elif auto_detect:
        # Auto-detection: try local first, then cloud
        print("🔍 Auto-detecting environment...")
        
        if check_local_server_status():
            API_URL = LOCAL_API_URL
            print(f"✅ Local server detected and accessible: {API_URL}")
            return True
        
        elif check_cloud_server_status():
            API_URL = CLOUD_API_URL
            print(f"✅ Using cloud environment: {API_URL}")
            print("💡 (Local server not running - to test locally, run: poetry run python main.py)")
            return True
        
        else:
            print(f"❌ Neither local ({LOCAL_API_URL}) nor cloud ({CLOUD_API_URL}) servers are accessible")
            return False
    
    else:
        # Default behavior: use cloud deployment
        print("🌐 Using default CLOUD environment for testing...")
        if check_cloud_server_status():
            API_URL = CLOUD_API_URL
            print(f"✅ Cloud server accessible: {API_URL}")
            print("💡 (Use --local to test locally, or --auto to auto-detect environment)")
            return True
        else:
            print(f"❌ Cloud server not accessible at {CLOUD_API_URL}")
            print("💡 Trying local server as fallback...")
            if check_local_server_status():
                API_URL = LOCAL_API_URL
                print(f"✅ Fallback to local server: {API_URL}")
                return True
            else:
                print(f"❌ Neither cloud nor local servers are accessible")
                return False

def show_environment_status():
    """Show the status of both local and cloud environments"""
    print("🔍 Environment Status Check")
    print("=" * 50)
    
    # Check local
    print(f"🏠 Local Server ({LOCAL_API_URL}):")
    if check_local_server_status():
        print("   ✅ Running and accessible")
    else:
        print("   ❌ Not running or not accessible")
        print("   💡 To start locally: poetry run python main.py")
    
    # Check cloud
    print(f"\n☁️  Cloud Server ({CLOUD_API_URL}):")
    if check_cloud_server_status():
        print("   ✅ Running and accessible")
    else:
        print("   ❌ Not accessible")
    
    print("\n🔧 Environment Variables:")
    print(f"   LOCAL_API_URL: {LOCAL_API_URL}")
    print(f"   CLOUD_API_URL: {CLOUD_API_URL}")
    print("\n💡 You can override URLs with environment variables:")
    print("   export LOCAL_API_URL=http://localhost:3000")
    print("   export CLOUD_API_URL=https://your-custom-url.app")
    print()

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

def save_test_results(config, result_type=None, brand=None, product_name=None, ingredients=None, nutrition_facts=None, allergens=None, dietary_claims=None, weight_data=None):
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
        if "weight_analysis" not in config:
            config["weight_analysis"] = {}
        
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
                
        elif result_type == "weight" and weight_data is not None:
            config["weight_analysis"]["net_weight"] = weight_data.get("net_weight")
            config["weight_analysis"]["package_count"] = weight_data.get("package_count")
            config["weight_analysis"]["serving_info"] = weight_data.get("serving_info")
            config["weight_analysis"]["weight_unit"] = weight_data.get("weight_unit")
            config["weight_analysis"]["numerical_value"] = weight_data.get("numerical_value")
            config["weight_analysis"]["additional_weights"] = weight_data.get("additional_weights", [])
        
        # Clean up old format fields if they exist
        old_fields = ["brand", "product_name", "ingredients", "nutrition_facts", "allergens", "dietary_claims", "net_weight", "package_count"]
        for field in old_fields:
            if field in config and field != "bar_code":
                # Only remove if the data has been moved to the new structure
                if ((field in ["brand", "product_name"] and config["product_analysis"]) or
                    (field == "ingredients" and config["ingredients_analysis"]) or
                    (field in ["nutrition_facts", "allergens", "dietary_claims"] and config["nutrition_analysis"]) or
                    (field in ["net_weight", "package_count"] and config["weight_analysis"])):
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
        elif result_type == "weight" and weight_data is not None:
            net_weight = weight_data.get('net_weight', 'N/A')
            package_count = weight_data.get('package_count', 'N/A')
            serving_info = weight_data.get('serving_info', 'N/A')
            additional_weights = weight_data.get('additional_weights', [])
            print(f"   Net Weight: {net_weight}")
            if package_count != 'N/A':
                print(f"   Package Count: {package_count}")
            if serving_info != 'N/A':
                print(f"   Serving Info: {serving_info}")
            if additional_weights and len(additional_weights) > 0:
                print(f"   Additional Weights: {', '.join(additional_weights)}")
        
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

def test_weight_analysis(image_path):
    """Test the weight analysis endpoint with an image file"""
    
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
            
            print(f"🔄 Analyzing weight image: {image_path}")
            print(f"🏷️  Using barcode: {bar_code}")
            print(f"📡 Sending request to: {API_URL}/get-weight")
            
            # Send POST request to get-weight endpoint
            response = requests.post(
                f"{API_URL}/get-weight",
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            # Parse and display the response
            if response.status_code == 200:
                result = response.json()
                print("✅ Weight analysis completed successfully!")
                print(json.dumps(result, indent=2))
                
                if result.get('success'):
                    data = result.get('data', {})
                    net_weight = data.get('net_weight', 'N/A')
                    package_count = data.get('package_count', 'N/A')
                    serving_info = data.get('serving_info', 'N/A')
                    weight_unit = data.get('weight_unit', 'N/A')
                    numerical_value = data.get('numerical_value', 'N/A')
                    additional_weights = data.get('additional_weights', [])
                    confidence = data.get('confidence', 'N/A')
                    
                    print(f"\n⚖️  Net Weight: {net_weight}")
                    print(f"🎯 Confidence: {confidence}")
                    if package_count != 'N/A':
                        print(f"📦 Package Count: {package_count}")
                    if serving_info != 'N/A':
                        print(f"🍽️  Serving Info: {serving_info}")
                    if weight_unit != 'N/A' and numerical_value != 'N/A':
                        print(f"📏 Unit: {weight_unit}, Value: {numerical_value}")
                    
                    # Display additional weights if found
                    if additional_weights and len(additional_weights) > 0:
                        print(f"\n📋 Additional Weights Found:")
                        for i, weight in enumerate(additional_weights, 1):
                            print(f"   {i}. {weight}")
                    
                    # Save weight results to input.json if analysis was successful
                    if net_weight != 'N/A':
                        save_test_results(config, result_type="weight", weight_data=data)
                    
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
    
    if not API_URL:
        print("❌ No API URL available for testing")
        return
    
    endpoints = [
        ("Root", "/"),
        ("Health Check", "/health"),
        ("API Info", "/info")
    ]
    
    print(f"🧪 Testing all endpoints on {API_URL}...\n")
    
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

def test_weight_with_default_image():
    """Test weight endpoint with default Amul ice cream front image (as it shows weight info)"""
    script_dir = Path(__file__).parent
    weight_image = script_dir / "test_data" / "nutrition_amul_icecream.jpg"
    
    print("⚖️  Testing Weight Extraction with default image")
    print("-" * 50)
    
    if weight_image.exists():
        test_weight_analysis(str(weight_image))
    else:
        print(f"❌ Test image not found: {weight_image}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Test script for EatGrediant AI API endpoints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Default: use cloud environment
  python test_product_analysis.py --product
  python test_product_analysis.py --ingredients
  
  # Force specific environment
  python test_product_analysis.py --local --product
  python test_product_analysis.py --cloud --nutrition
  
  # Auto-detect environment (tries local first, then cloud)
  python test_product_analysis.py --auto --product
  
  # Test custom image
  python test_product_analysis.py my_image.jpg
  python test_product_analysis.py --local my_image.jpg
  
  # Check environment status
  python test_product_analysis.py --status
  
Environment Variables:
  LOCAL_API_URL: Override local API URL (default: http://localhost:8000)
  CLOUD_API_URL: Override cloud API URL (default: https://eatgrediant-ai-api-tc5cvwjylq-uc.a.run.app)
'''
    )
    
    # Environment selection (mutually exclusive)
    env_group = parser.add_mutually_exclusive_group()
    env_group.add_argument('--local', action='store_true', help='Force testing on local server')
    env_group.add_argument('--cloud', action='store_true', help='Force testing on cloud server')
    env_group.add_argument('--auto', action='store_true', help='Auto-detect environment (try local first, then cloud)')
    
    # Test type selection (mutually exclusive)
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument('--product', action='store_true', help='Test product name endpoint with default image')
    test_group.add_argument('--ingredients', action='store_true', help='Test ingredients endpoint with default image')
    test_group.add_argument('--nutrition', action='store_true', help='Test nutrition endpoint with default image')
    test_group.add_argument('--weight', action='store_true', help='Test weight endpoint with default image')
    test_group.add_argument('--status', action='store_true', help='Show environment status')
    
    # Image path (positional argument)
    parser.add_argument('image_path', nargs='?', help='Path to image file for product name testing')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    print("🚀 EatGrediant AI API - Product Analysis Test")
    print("=" * 50)
    
    # Handle status check first
    if args.status:
        show_environment_status()
        return
    
    # Select API URL based on arguments
    if not select_api_url(force_local=args.local, force_cloud=args.cloud, auto_detect=args.auto):
        sys.exit(1)
    
    print()
    
    # Test basic endpoints first
    test_all_endpoints()
    
    # Handle specific test requests
    if args.product:
        test_product_with_default_image()
    elif args.ingredients:
        test_ingredients_with_default_image()
    elif args.nutrition:
        test_nutrition_with_default_image()
    elif args.weight:
        test_weight_with_default_image()
    elif args.image_path:
        # Test product name endpoint with custom image
        print("📦 Testing Product Name Extraction with custom image")
        print("-" * 50)
        test_product_analysis(args.image_path)
    else:
        # No specific test requested - run all tests with default images
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
        
        # Test weight endpoint
        print("\n⚖️  Testing Weight Endpoint")
        test_weight_with_default_image()
        
        print("\n" + "=" * 60)
        print("✅ All endpoint testing completed!")
        
        print("\n📝 Individual Usage Options:")
        print("  python test_product_analysis.py --product          # Test product name only (cloud by default)")
        print("  python test_product_analysis.py --ingredients      # Test ingredients only (cloud by default)")
        print("  python test_product_analysis.py --nutrition        # Test nutrition only (cloud by default)")
        print("  python test_product_analysis.py --weight           # Test weight only (cloud by default)")
        print("  python test_product_analysis.py <image_path>       # Test product name with custom image (cloud by default)")
        print("\n🌐 Environment Options:")
        print("  python test_product_analysis.py --local --product  # Force local testing")
        print("  python test_product_analysis.py --cloud --product  # Force cloud testing (explicit)")
        print("  python test_product_analysis.py --auto --product   # Auto-detect environment")
        print("  python test_product_analysis.py --status           # Check environment status")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

# Legacy support for old command line usage
# This section is kept for backward compatibility but will be removed in the new version
if False:  # Disabled - using argparse instead
    # Handle different command line arguments
    if len(sys.argv) == 1:
        pass  # This old code is now handled by the main() function
