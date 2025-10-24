#!/bin/bash

# EatGrediant AI API - Poetry Setup Script
# This script initializes Poetry, adds dependencies, and runs the FastAPI app locally

set -e  # Exit on any error

echo "🚀 Setting up EatGrediant AI API with Poetry..."

# Set up PATH to include Poetry
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first:"
    echo "   pip3 install poetry"
    echo "   Or visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo "✅ Poetry is installed"

# Initialize Poetry project if pyproject.toml doesn't exist
if [ ! -f "pyproject.toml" ]; then
    echo "📦 Initializing Poetry project..."
    poetry init --no-interaction
    
    # Add package-mode = false to avoid packaging issues
    echo "" >> pyproject.toml
    echo "[tool.poetry]" >> pyproject.toml
    echo "package-mode = false" >> pyproject.toml
    
    echo "✅ Poetry project initialized"
else
    echo "✅ Poetry project already exists"
fi

# Add dependencies from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "📋 Adding dependencies from requirements.txt..."
    
    # Read each line from requirements.txt and add to Poetry
    while IFS= read -r line || [ -n "$line" ]; do
        # Remove leading/trailing whitespace
        line=$(echo "$line" | xargs)
        
        # Skip empty lines and comments
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            echo "   Adding: $line"
            
            # Try to add the dependency, handle potential errors gracefully
            if poetry add "$line"; then
                echo "   ✅ Successfully added $line"
            else
                echo "   ❌ Failed to add $line, trying without version constraints..."
                # Extract package name only (remove version specifiers)
                package_name=$(echo "$line" | sed 's/[>=<\[!].*//' | sed 's/==.*//')
                poetry add "$package_name" || echo "   ❌ Failed to add $package_name"
            fi
        fi
    done < requirements.txt
    
    echo "✅ Dependencies processed from requirements.txt"
fi

# Install dependencies
echo "🔧 Installing dependencies..."
poetry install --no-root

# Check if virtual environment was created
echo "🌍 Virtual environment info:"
poetry env info

# Create a simple run script
echo "📝 Creating run script..."
cat > run_app.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting EatGrediant AI API..."
cd .. && poetry run python main.py
EOF

chmod +x run_app.sh

echo ""
echo "✅ Setup complete! Your FastAPI app is ready."
echo ""
echo "🔹 To run the app:"
echo "   ./run_app.sh"
echo "   or"
echo "   poetry run python main.py"
echo ""
echo "🔹 To activate the virtual environment:"
echo "   poetry shell"
echo ""
echo "🔹 To add more dependencies:"
echo "   poetry add package-name"
echo ""
echo "🔹 The app will be available at: http://localhost:8000"
echo ""
echo "🚀 Starting the application..."
cd .. && poetry run python main.py