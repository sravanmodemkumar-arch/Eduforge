#!/bin/bash
# ============================================================
# EduForge — GitHub Repository Setup Script
# Run this locally with: bash scripts/setup-github.sh
# Requires: gh CLI (brew install gh / sudo apt install gh)
# ============================================================

set -euo pipefail

REPO="sravanmodemkumar-arch/Eduforge"

echo "================================================"
echo "  EduForge — GitHub Repository Setup"
echo "================================================"
echo ""

# ── Step 1: Rename branches ─────────────────────────────────
echo "▶ Step 1: Renaming branches..."

gh api -X POST "repos/${REPO}/branches/claude%2Fmain-Eu3LV/rename" \
  -f new_name="main" 2>/dev/null && echo "  ✓ claude/main-Eu3LV → main" || echo "  ⚠ main already exists or rename failed"

gh api -X POST "repos/${REPO}/branches/claude%2Fdevelop-Eu3LV/rename" \
  -f new_name="develop" 2>/dev/null && echo "  ✓ claude/develop-Eu3LV → develop" || echo "  ⚠ develop already exists or rename failed"

gh api -X POST "repos/${REPO}/branches/claude%2Fqa-Eu3LV/rename" \
  -f new_name="qa" 2>/dev/null && echo "  ✓ claude/qa-Eu3LV → qa" || echo "  ⚠ qa already exists or rename failed"

gh api -X POST "repos/${REPO}/branches/claude%2Fprod-Eu3LV/rename" \
  -f new_name="prod" 2>/dev/null && echo "  ✓ claude/prod-Eu3LV → prod" || echo "  ⚠ prod already exists or rename failed"

echo ""

# ── Step 2: Set default branch to main ──────────────────────
echo "▶ Step 2: Setting main as default branch..."

gh api -X PATCH "repos/${REPO}" \
  -f default_branch="main" && echo "  ✓ Default branch set to main"

echo ""

# ── Step 3: Enable repo features ────────────────────────────
echo "▶ Step 3: Configuring repository settings..."

gh api -X PATCH "repos/${REPO}" \
  -F delete_branch_on_merge=true \
  -F allow_squash_merge=true \
  -F allow_merge_commit=true \
  -F allow_rebase_merge=false \
  -F allow_auto_merge=true \
  -F has_issues=true \
  -F has_projects=true \
  -F has_wiki=false \
  && echo "  ✓ Repo settings updated (delete branch on merge, squash merge enabled)"

echo ""

# ── Step 4: Branch protection — main ────────────────────────
echo "▶ Step 4: Adding branch protection rules..."

echo "  Setting up main branch protection..."
gh api -X PUT "repos/${REPO}/branches/main/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint-and-test (identity)", "lint-and-test (exam)", "lint-portal", "build-images (portal)"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "  ✓ main: Require PR + 1 approval + CI pass, no force push"

echo ""
echo "  Setting up develop branch protection..."
gh api -X PUT "repos/${REPO}/branches/develop/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "  ✓ develop: Require PR + 1 approval, no force push"

echo ""
echo "  Setting up qa branch protection..."
gh api -X PUT "repos/${REPO}/branches/qa/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "  ✓ qa: Require PR + 1 approval + dismiss stale, no force push"

echo ""
echo "  Setting up prod branch protection..."
gh api -X PUT "repos/${REPO}/branches/prod/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint-and-test (identity)", "lint-and-test (exam)", "lint-portal", "build-images (portal)"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
echo "  ✓ prod: Require PR + 2 approvals + CI pass + enforce admins, no force push"

echo ""

# ── Step 5: Create labels ───────────────────────────────────
echo "▶ Step 5: Creating issue labels..."

declare -A LABELS=(
  ["service:identity"]="0052CC"
  ["service:portal"]="1D76DB"
  ["service:exam"]="5319E7"
  ["service:notification"]="FBCA04"
  ["service:billing"]="0E8A16"
  ["service:ai"]="D93F0B"
  ["service:analytics"]="C5DEF5"
  ["service:mobile"]="F9D0C4"
  ["priority:critical"]="B60205"
  ["priority:high"]="D93F0B"
  ["priority:medium"]="FBCA04"
  ["priority:low"]="0E8A16"
  ["type:bug"]="D73A4A"
  ["type:feature"]="0075CA"
  ["type:refactor"]="CFD3D7"
  ["type:docs"]="0075CA"
  ["type:infra"]="E4E669"
  ["env:dev"]="BFD4F2"
  ["env:qa"]="BFDADC"
  ["env:prod"]="F9D0C4"
)

for label in "${!LABELS[@]}"; do
  gh label create "$label" --repo "$REPO" --color "${LABELS[$label]}" --force 2>/dev/null \
    && echo "  ✓ Created label: $label" \
    || echo "  ⚠ Label $label may already exist"
done

echo ""

# ── Step 6: Delete old claude/ branches ──────────────────────
echo "▶ Step 6: Cleaning up old branches..."

for branch in claude/initial-commit-Eu3LV; do
  gh api -X DELETE "repos/${REPO}/git/refs/heads/${branch}" 2>/dev/null \
    && echo "  ✓ Deleted ${branch}" \
    || echo "  ⚠ ${branch} not found or already deleted"
done

echo ""

# ── Summary ──────────────────────────────────────────────────
echo "================================================"
echo "  ✅ GitHub Setup Complete!"
echo "================================================"
echo ""
echo "  Branches:"
echo "    main    (default) — require PR + 1 approval + CI"
echo "    develop           — require PR + 1 approval"
echo "    qa                — require PR + 1 approval"
echo "    prod              — require PR + 2 approvals + CI"
echo ""
echo "  Git flow:"
echo "    feature/* → develop → qa → prod → main"
echo ""
echo "  Repo settings:"
echo "    ✓ Delete branch on merge"
echo "    ✓ Squash merge enabled"
echo "    ✓ Auto-merge enabled"
echo "    ✓ Force push blocked on all branches"
echo ""
echo "  Next: Update your local repo:"
echo "    git fetch origin"
echo "    git checkout main"
echo "    git branch -D claude/main-Eu3LV claude/develop-Eu3LV claude/qa-Eu3LV claude/prod-Eu3LV"
echo ""
