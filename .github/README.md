# GitHub Actions Workflows

## Sync from Upstream

**File:** `.github/workflows/sync-upstream.yml`

### Purpose
Automatically synchronizes changes from the upstream repository (sl1nabd/Emergent:main) into this repository.

### How It Works
1. **Scheduled Runs**: The workflow runs automatically every hour (on the hour)
2. **Manual Trigger**: Can also be triggered manually from the GitHub Actions tab
3. **Change Detection**: Checks if there are new commits in the upstream repository
4. **Automatic Merge**: If changes are detected, it attempts to merge them automatically
5. **Push**: Successfully merged changes are pushed to the current branch

### Workflow Steps
1. Checkout the current repository with full history
2. Configure git with GitHub Actions bot credentials
3. Add sl1nabd/Emergent as an upstream remote
4. Fetch the latest changes from upstream/main
5. Check if there are any new commits to merge
6. Merge changes if found (with automatic conflict detection)
7. Push merged changes back to the repository

### Conflict Handling
If the workflow encounters merge conflicts:
- The workflow will fail with an error message
- You'll need to manually resolve the conflicts
- The workflow will retry on the next scheduled run or manual trigger

### Manual Triggering
To manually trigger the sync:
1. Go to the "Actions" tab in the GitHub repository
2. Select "Sync from Upstream" workflow
3. Click "Run workflow"
4. Select the branch and click "Run workflow"

### Configuration
The workflow can be customized by editing `.github/workflows/sync-upstream.yml`:
- **Schedule**: Change the `cron` expression to adjust the frequency
- **Branch**: Modify which branch receives the synced changes
- **Merge Strategy**: Adjust merge options if needed

### Requirements
- No special secrets or permissions required beyond `GITHUB_TOKEN`
- The workflow uses the default `GITHUB_TOKEN` provided by GitHub Actions
