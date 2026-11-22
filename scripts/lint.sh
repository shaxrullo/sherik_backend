#!/bin/bash

# Linting and Code Quality Script
# Runs various code quality checks

set -e  # Exit on first error

echo "================================"
echo "Backend Sherik - Code Quality Checks"
echo "================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: Run this script from the project root directory${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}1. Checking Python syntax with Pylint...${NC}"
if command -v pylint &> /dev/null; then
    pylint listings/ favorites/ reports/ matching/ users/ config/ --disable=all --enable=syntax-error || true
else
    echo -e "${YELLOW}   Pylint not installed, skipping...${NC}"
fi

echo ""
echo -e "${YELLOW}2. Code formatting check with Black...${NC}"
if command -v black &> /dev/null; then
    black --check --diff --color . --exclude venv,migrations || {
        echo -e "${YELLOW}   Run 'black .' to fix formatting issues${NC}"
    }
else
    echo -e "${RED}   Black not installed: pip install black${NC}"
fi

echo ""
echo -e "${YELLOW}3. Import sorting check with isort...${NC}"
if command -v isort &> /dev/null; then
    isort --check . --exclude venv,migrations --diff || {
        echo -e "${YELLOW}   Run 'isort .' to fix import ordering${NC}"
    }
else
    echo -e "${RED}   isort not installed: pip install isort${NC}"
fi

echo ""
echo -e "${YELLOW}4. Code linting with flake8...${NC}"
if command -v flake8 &> /dev/null; then
    flake8 listings/ favorites/ reports/ matching/ users/ config/ \
        --max-line-length=100 \
        --exclude=migrations,__pycache__,.venv \
        --ignore=E203,W503,E501 \
        --statistics || {
        echo -e "${YELLOW}   Some linting issues found (review above)${NC}"
    }
else
    echo -e "${RED}   flake8 not installed: pip install flake8${NC}"
fi

echo ""
echo -e "${YELLOW}5. Security check with bandit...${NC}"
if command -v bandit &> /dev/null; then
    bandit -r listings/ favorites/ reports/ matching/ users/ config/ \
        -ll -v || {
        echo -e "${YELLOW}   Some security issues found (review above)${NC}"
    }
else
    echo -e "${RED}   bandit not installed: pip install bandit${NC}"
fi

echo ""
echo -e "${YELLOW}6. Database checks...${NC}"
python manage.py check --deploy --fail-level WARNING || true

echo ""
echo -e "${YELLOW}7. Missing migrations check...${NC}"
python manage.py makemigrations --dry-run --check || {
    echo -e "${RED}   Missing migrations detected!${NC}"
}

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Code quality checks completed!${NC}"
echo -e "${GREEN}================================${NC}"

echo ""
echo "To auto-fix some issues:"
echo "  black .          # Format code"
echo "  isort .          # Sort imports"
echo ""
echo "Before committing, make sure all checks pass!"
