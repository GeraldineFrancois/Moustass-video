#!/bin/bash
# Script pour exécuter les tests avec coverage et générer les rapports

set -e  # Exit on error

echo "🧪 Moustass Video - Test Suite Runner"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Clean previous reports
echo -e "${YELLOW}📂 Cleaning previous test reports...${NC}"
rm -rf htmlcov .pytest_cache .coverage coverage.xml
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 2: Run pytest with coverage
echo -e "${YELLOW}🧪 Running tests with coverage...${NC}"
echo ""

# Run all tests
pytest tests/ -v \
    --cov=src \
    --cov-report=xml:coverage.xml \
    --cov-report=html:htmlcov \
    --cov-report=term-missing \
    --cov-branch \
    --tb=short \
    -m "not slow"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed!${NC}"
fi
echo ""

# Step 3: Display coverage summary
echo -e "${YELLOW}📊 Coverage Summary:${NC}"
coverage report --skip-empty --precision=2
echo ""

# Step 4: Check coverage thresholds
echo -e "${YELLOW}🎯 Checking coverage thresholds...${NC}"
COVERAGE_PERCENT=$(coverage report --precision=0 | grep TOTAL | awk '{print $4}' | sed 's/%//')

if [ "$COVERAGE_PERCENT" -ge 80 ]; then
    echo -e "${GREEN}✓ Coverage is ${COVERAGE_PERCENT}% (target: 80%)${NC}"
elif [ "$COVERAGE_PERCENT" -ge 60 ]; then
    echo -e "${YELLOW}⚠ Coverage is ${COVERAGE_PERCENT}% (target: 80%)${NC}"
else
    echo -e "${RED}✗ Coverage is ${COVERAGE_PERCENT}% (target: 80%)${NC}"
fi
echo ""

# Step 5: Generate reports info
echo -e "${YELLOW}📁 Generated reports:${NC}"
echo "  - XML report (for SonarQube): coverage.xml"
echo "  - HTML report: htmlcov/index.html"
echo ""

# Step 6: Display next steps
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "  1. View HTML report: open htmlcov/index.html"
echo "  2. Run SonarQube scan: sonar-scanner"
echo "  3. Run specific tests: pytest tests/auth/test_security.py -v"
echo "  4. Run with markers: pytest -m security"
echo ""

# Exit with test exit code
exit $TEST_EXIT_CODE
