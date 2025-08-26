#!/bin/bash

# Baltic Exchange Scraper - Vercel Deployment Script

echo "🚀 Preparing Baltic Exchange Scraper for Vercel deployment..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Please install it first:"
    echo "   npm i -g vercel"
    exit 1
fi

# Clean up any previous builds
echo "🧹 Cleaning up previous builds..."
rm -rf .vercel

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements-vercel.txt

# Test the application locally
echo "🧪 Testing application locally..."
python3 -c "
import sys
sys.path.append('src')
from main import app
print('✅ FastAPI app imported successfully')
"

if [ $? -eq 0 ]; then
    echo "✅ Local test passed"
else
    echo "❌ Local test failed"
    exit 1
fi

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

echo "🎉 Deployment complete!"
echo "📱 Your app should be live at the URL provided above"
