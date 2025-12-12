#!/bin/bash
# Setup script for terminal chat app

set -e

echo "🚀 Setting up Terminal Chat App..."
echo ""

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install
echo ""

# Check for secrets
echo "🔍 Checking for secrets..."
./check-secrets.sh
echo ""

# Create .env.local from example if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local from env.example..."
    cp env.example .env.local
    echo "✅ Created .env.local - please edit it with your AI_MODEL configuration"
    echo ""
fi

# Initialize git if not already done
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
    echo ""
fi

# Create pre-commit hook
if [ -d .git/hooks ]; then
    echo "📝 Creating pre-commit hook..."
    cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
./check-secrets.sh
if [ $? -ne 0 ]; then
  echo ""
  echo "❌ Commit blocked: Secrets detected!"
  echo "Please remove secrets before committing."
  exit 1
fi
HOOK
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook created"
    echo ""
fi

echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.local and set your AI_MODEL"
echo "2. Run 'npm run dev' to start development server"
echo "3. Run './check-secrets.sh' before committing to GitHub"
echo "4. See DEPLOYMENT.md for Vercel deployment instructions"
echo ""

