#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build Tailwind CSS
echo "Installing Node.js dependencies..."
npm install

echo "Building Tailwind CSS..."
npm run build

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations if needed
echo "Running migrations..."
python manage.py migrate --noinput

echo "Build completed successfully."