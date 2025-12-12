#!/bin/bash
# Script to check for API keys and secrets before committing

echo "🔍 Checking for API keys and secrets..."

# Patterns to check for
PATTERNS=(
  "api[_-]?key\s*[:=]\s*['\"][^'\"]{20,}"
  "secret\s*[:=]\s*['\"][^'\"]{20,}"
  "token\s*[:=]\s*['\"][^'\"]{20,}"
  "password\s*[:=]\s*['\"][^'\"]{8,}"
  "auth\s*[:=]\s*['\"][^'\"]{20,}"
  "sk-[a-zA-Z0-9]{32,}"
  "xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{32}"
  "AKIA[0-9A-Z]{16}"
  "ghp_[a-zA-Z0-9]{36}"
  "gho_[a-zA-Z0-9]{36}"
)

FOUND_SECRETS=false

# Check all files except node_modules, venv, .git, and build directories
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.json" -o -name "*.env*" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/venv/*" \
  ! -path "*/.git/*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -name "package-lock.json" \
  ! -name "yarn.lock" | while read file; do
  
  for pattern in "${PATTERNS[@]}"; do
    if grep -qiE "$pattern" "$file" 2>/dev/null; then
      echo "⚠️  Potential secret found in: $file"
      echo "   Pattern: $pattern"
      grep -niE "$pattern" "$file" 2>/dev/null | head -3
      echo ""
      FOUND_SECRETS=true
    fi
  done
done

if [ "$FOUND_SECRETS" = true ]; then
  echo "❌ Secrets found! Please remove them before committing."
  exit 1
else
  echo "✅ No secrets found. Safe to commit!"
  exit 0
fi
