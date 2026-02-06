#!/bin/bash

# Commit all changes and push to remote
# Usage: ./commit-push.sh "your commit message"

if [ -z "$1" ]; then
    echo "Error: Commit message required"
    echo "Usage: ./commit-push.sh \"your commit message\""
    exit 1
fi

git add -A
git commit -m "$1"
git push
