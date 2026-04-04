#!/bin/bash

# Remove __pycache__ directories and .pyc files
git rm --cached -r "**/__pycache__/" "**/*.pyc"

# Remove coverage files
git rm --cached .coverage coverage.json

# Remove test reports
git rm --cached test-report.html test-report.json

# Remove test report directories if they exist
if [ -d "test-reports" ]; then
  git rm --cached -r test-reports/
fi

# Remove coverage_html directory if it exists
if [ -d "coverage_html" ]; then
  git rm --cached -r coverage_html/
fi

echo "Files removed from git tracking but kept on disk."
echo "Run 'git status' to see the changes."
echo "Commit these changes to finalize the removal from repository history."
