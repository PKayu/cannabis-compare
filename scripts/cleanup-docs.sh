#!/bin/bash

###############################################################################
# Documentation Cleanup Script
# Purpose: Maintain documentation consistency, organization, and update progress
# Usage: bash scripts/cleanup-docs.sh
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track issues found
ISSUES_FOUND=0
WARNINGS_FOUND=0

# Helper functions
print_header() {
  echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
  ((WARNINGS_FOUND++))
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
  ((ISSUES_FOUND++))
}

###############################################################################
# 1. NAMING CONVENTIONS CHECK
###############################################################################
check_naming_conventions() {
  print_header "1. Checking Naming Conventions"

  local conventions_ok=true

  # Check root level docs
  if [ -d "docs" ]; then
    for file in docs/*.md; do
      if [ -f "$file" ]; then
        filename=$(basename "$file")
        # Root level should be clear naming: API_TEST_PLAN, ARCHITECTURE, etc.
        if ! [[ "$filename" =~ ^[A-Z][A-Za-z0-9_]*\.md$ ]] && ! [[ "$filename" =~ ^[a-z][a-z_]*\.md$ ]]; then
          print_warning "Root doc naming: $filename (consider UPPERCASE_SNAKE_CASE or lowercase)"
          conventions_ok=false
        fi
      fi
    done
  fi

  # Check workflows - should be NN_description_STATUS.md
  if [ -d "docs/workflows" ]; then
    for file in docs/workflows/*.md; do
      if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "README.md" ]; then
          if ! [[ "$filename" =~ ^[0-9]{2}_[a-z_]+_(COMPLETED|IN_PROGRESS|PENDING)\.md$ ]]; then
            print_warning "Workflow naming: $filename (expected NN_description_STATUS.md)"
            conventions_ok=false
          fi
        fi
      fi
    done
  fi

  if [ "$conventions_ok" = true ]; then
    print_success "All files follow naming conventions"
  fi
}

###############################################################################
# 2. FILE ORGANIZATION CHECK
###############################################################################
check_file_organization() {
  print_header "2. Checking File Organization"

  local org_ok=true

  # Expected directories
  local expected_dirs=(
    "docs"
    "docs/workflows"
    "docs/archive"
  )

  for dir in "${expected_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
      print_error "Missing directory: $dir"
      org_ok=false
    fi
  done

  if [ "$org_ok" = true ]; then
    print_success "File organization is correct"
  fi
}

###############################################################################
# 3. REDUNDANCY CHECK
###############################################################################
check_redundancy() {
  print_header "3. Checking for Redundancy"

  local redundancy_ok=true

  # Check for TODO/FIXME markers that indicate incomplete docs
  todo_count=$(grep -r "TODO\|FIXME\|XXX" docs --include="*.md" 2>/dev/null | wc -l)
  if [ "$todo_count" -gt 0 ]; then
    print_warning "Found $todo_count TODO/FIXME markers in documentation"
    redundancy_ok=false
  fi

  # Check for placeholder text
  placeholder_count=$(grep -r "\[PLACEHOLDER\]\|\[TBD\]" docs --include="*.md" 2>/dev/null | wc -l)
  if [ "$placeholder_count" -gt 0 ]; then
    print_warning "Found $placeholder_count placeholder text sections in documentation"
    redundancy_ok=false
  fi

  if [ "$redundancy_ok" = true ]; then
    print_success "No obvious redundancy or incomplete sections found"
  fi
}

###############################################################################
# 4. WORKFLOW PROGRESS UPDATE
###############################################################################
update_workflow_progress() {
  print_header "4. Analyzing Workflow Progress"

  # Count completed workflows
  local completed=0
  local in_progress=0
  local pending=0
  local total=0

  if [ -d "docs/workflows" ]; then
    for file in docs/workflows/*.md; do
      if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "README.md" ]; then
          ((total++))
          if grep -q "COMPLETED" "$file" 2>/dev/null; then
            ((completed++))
          elif grep -q "IN_PROGRESS" "$file" 2>/dev/null; then
            ((in_progress++))
          else
            ((pending++))
          fi
        fi
      fi
    done
  fi

  echo "  Completed: $completed/$total"
  echo "  In Progress: $in_progress/$total"
  echo "  Pending: $pending/$total"

  local total_complete=$((completed + in_progress))
  if [ "$total" -gt 0 ]; then
    local progress_pct=$((total_complete * 100 / total))
    echo -e "${GREEN}  Overall Progress: ${progress_pct}%${NC}"
  fi

  print_success "Workflow progress analyzed"
}

###############################################################################
# 5. DOCUMENTATION HEALTH REPORT
###############################################################################
generate_health_report() {
  print_header "5. Documentation Health Report"

  local total_docs=$(find docs -type f -name "*.md" 2>/dev/null | wc -l)
  local root_docs=$(find docs -maxdepth 1 -type f -name "*.md" 2>/dev/null | wc -l)
  local workflow_docs=$(find docs/workflows -type f -name "*.md" 2>/dev/null | wc -l)
  local archived_docs=$(find docs/archive -type f -name "*.md" 2>/dev/null | wc -l)

  echo "  Total Documentation Files: $total_docs"
  echo "  Root Level: $root_docs"
  echo "  Workflows: $workflow_docs"
  echo "  Archived: $archived_docs"

  print_success "Documentation health report generated"
}

###############################################################################
# 6. MISSING SECTIONS CHECK
###############################################################################
check_critical_files() {
  print_header "6. Checking for Critical Files"

  local critical_ok=true

  local critical_files=(
    "docs/ARCHITECTURE.md"
    "docs/GETTING_STARTED.md"
    "docs/prd.md"
    "docs/workflows/README.md"
    "CLAUDE.md"
  )

  for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
      print_success "Found: $file"
    else
      print_error "Missing: $file"
      critical_ok=false
    fi
  done
}

###############################################################################
# 7. GENERATE SUMMARY
###############################################################################
generate_summary() {
  print_header "7. Summary"
  echo ""

  if [ $ISSUES_FOUND -eq 0 ] && [ $WARNINGS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ Documentation is in excellent shape!${NC}"
  elif [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS_FOUND warnings found (review recommended)${NC}"
  else
    echo -e "${RED}✗ $ISSUES_FOUND issues found (action recommended)${NC}"
    echo -e "${YELLOW}⚠ $WARNINGS_FOUND warnings found${NC}"
  fi

  echo ""
  echo "Recommendations:"
  echo "  1. Review warnings above and address naming/organization issues"
  echo "  2. Archive outdated documentation to docs/archive/"
  echo "  3. Review very old files and update if needed"
  echo "  4. Resolve any TODO/FIXME markers"
  echo ""
  echo "To commit changes:"
  echo "  git add docs/"
  echo "  git commit -m 'docs: cleanup and reorganization'"
  echo ""
}

###############################################################################
# MAIN EXECUTION
###############################################################################
main() {
  echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
  echo -e "${BLUE}║   Documentation Cleanup Script 📚      ║${NC}"
  echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
  echo ""

  # Run all checks
  check_naming_conventions
  echo ""

  check_file_organization
  echo ""

  check_redundancy
  echo ""

  update_workflow_progress
  echo ""

  generate_health_report
  echo ""

  check_critical_files
  echo ""

  generate_summary

  # Exit with appropriate code
  if [ $ISSUES_FOUND -gt 0 ]; then
    exit 1
  else
    exit 0
  fi
}

# Run main function
main
