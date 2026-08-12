#!/bin/sh
# COPY TEMPLATE — copy into .git/hooks/pre-commit, then make it executable:
#   cp assets/ci/pre-commit.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# Runs the same two design checks as assets/ci/design-lint.yml locally,
# before a commit is created. Aborts the commit if a check reports a
# violation (non-zero exit code). If an input file is missing, the
# corresponding check is skipped cleanly (no commit abort).
#
# Prerequisite: bulk_restyle.py and check_contrast.py live in the repo,
# e.g. under tools/design/ (copied from the skill: scripts/*.py).
# Adjust the paths below as needed.

TOOLS_DIR="tools/design"
REPORT_PATH="."
ALLOWED_FONTS="Segoe UI,Segoe UI Semibold"

status=0

if [ -f "design-out/zones.json" ]; then
    echo "Design lint: checking geometry/fonts/shadows..."
    python3 "${TOOLS_DIR}/bulk_restyle.py" "${REPORT_PATH}" \
        --check \
        --zones design-out/zones.json \
        --fonts "${ALLOWED_FONTS}"
    if [ $? -ne 0 ]; then
        status=1
    fi
else
    echo "Note: design-out/zones.json missing — design linter skipped."
fi

if [ -f "design-out/palette.json" ]; then
    echo "Contrast check: checking palette against WCAG AA..."
    python3 "${TOOLS_DIR}/check_contrast.py" --palette design-out/palette.json
    if [ $? -ne 0 ]; then
        status=1
    fi
else
    echo "Note: design-out/palette.json missing — contrast check skipped."
fi

if [ $status -ne 0 ]; then
    echo ""
    echo "Commit aborted: design checks reported violations (see above)."
    echo "Fix them, or deliberately bypass with 'git commit --no-verify'."
    exit 1
fi

exit 0
