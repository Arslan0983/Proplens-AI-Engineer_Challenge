#!/bin/bash

# Setup script for Proplens AI Engineer Challenge

echo "Setting up Proplens AI Engineer Challenge..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment is not activated!"
    echo "Please activate your virtual environment first:"
    echo "  source venv/bin/activate"
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Python not found. Please install Python 3.9+"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo "Please edit .env and add your GEMINI_API_KEY"
    else
        echo "Warning: .env.example not found. Creating basic .env file..."
        cat > .env << EOF
SECRET_KEY=your-secret-key-here
DEBUG=True
JWT_SECRET_KEY=your-jwt-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-pro
EOF
        echo "Please edit .env and add your GEMINI_API_KEY"
    fi
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p media/documents
mkdir -p chroma_db
mkdir -p staticfiles

# Run migrations
echo "Running database migrations..."
$PYTHON_CMD manage.py migrate

# Initialize database schema
echo "Initializing sample database schema..."
$PYTHON_CMD manage.py shell << EOF
from api.services.database_service import DatabaseService
DatabaseService.initialize_sample_schema()
print("Database schema initialized successfully!")
EOF

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure your virtual environment is activated"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Edit .env file and add your GEMINI_API_KEY"
echo "4. Run: python manage.py runserver"
echo "5. Visit: http://localhost:8000/api/docs"

