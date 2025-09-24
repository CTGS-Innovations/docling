#!/bin/bash

# Pipeline Performance Test Runner
# =================================
# Quick script to run performance isolation tests

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔬 MVP-Fusion Pipeline Performance Isolator${NC}"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "fusion_cli.py" ]; then
    echo -e "${RED}❌ Error: Must run from mvp-fusion directory${NC}"
    echo "Please run: cd /home/corey/projects/docling/mvp-fusion"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source .venv-clean/bin/activate

# Options
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./run_performance_test.sh [options]"
    echo ""
    echo "Options:"
    echo "  --full           Run complete test suite (default)"
    echo "  --quick          Run quick test with fewer documents"
    echo "  --stages 1,2,3   Run specific stages only"
    echo "  --config FILE    Use specific config file"
    echo ""
    exit 0
fi

# Default config
CONFIG="config/full.yaml"
STAGES=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            echo -e "${GREEN}⚡ Running quick test mode${NC}"
            # Modify the test to use fewer documents
            export QUICK_TEST=1
            shift
            ;;
        --stages)
            STAGES="--stages $2"
            echo -e "${GREEN}🎯 Running stages: $2${NC}"
            shift 2
            ;;
        --config)
            CONFIG="$2"
            echo -e "${GREEN}📄 Using config: $2${NC}"
            shift 2
            ;;
        --full|*)
            echo -e "${GREEN}📊 Running full test suite${NC}"
            shift
            ;;
    esac
done

echo ""
echo -e "${BLUE}Starting performance isolation test...${NC}"
echo "----------------------------------------"

# Run the test
python throwaway_tests/pipeline_performance_isolator.py --config "$CONFIG" $STAGES

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Test completed successfully!${NC}"
    echo ""
    echo "📄 Check the report at: ../output/performance_test/performance_report.json"
else
    echo ""
    echo -e "${RED}❌ Test failed - check errors above${NC}"
fi