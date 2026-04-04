#!/bin/bash

# Go to the repository root
cd "$(git rev-parse --show-toplevel)"

# Remove __pycache__ directories and .pyc files from gcpoto project
git rm --cached -r "gcpoto/**/__pycache__/" "gcpoto/**/*.pyc" 2>/dev/null || true

# Remove coverage files
git rm --cached "gcpoto/.coverage" "gcpoto/coverage.json" 2>/dev/null || true

# Remove test reports
git rm --cached "gcpoto/test-report.html" "gcpoto/test-report.json" 2>/dev/null || true

# Remove test report directories if they exist
git rm --cached -r "gcpoto/test-reports/" 2>/dev/null || true

# Remove coverage_html directory if it exists
git rm --cached -r "gcpoto/coverage_html/" 2>/dev/null || true

# Remove .pytest_cache directory if it exists
git rm --cached -r "gcpoto/.pytest_cache/" 2>/dev/null || true

echo "Files removed from git tracking but kept on disk."
echo "Run 'git status' to see the changes."
echo "Commit these changes to finalize the removal from repository history with:"
echo "git commit -m 'Remove ignored files from git tracking'"
