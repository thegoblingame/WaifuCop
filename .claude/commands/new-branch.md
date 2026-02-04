# New Branch Command

When the user invokes this command, perform the following steps:

1. Ask the user for the branch name if not provided
2. Fetch the latest changes from origin
3. Create a new branch from `main` and check it out

## Execution

```bash
git fetch origin
git checkout master
git pull origin master
git checkout -b <branch-name>
```

## Usage

User says: "new-branch" or "create branch <name>"
