#!/bin/bash

# Pull latest changes and create a new branch
# Usage: ./new-branch.sh "branch-name"

if [ -z "$1" ]; then
    echo "Error: Branch name required"
    echo "Usage: ./new-branch.sh \"branch-name\""
    exit 1
fi

git checkout main
git pull origin main
git checkout -b "$1"
