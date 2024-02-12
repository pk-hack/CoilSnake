#!/usr/bin/env python
import os
import subprocess
import sys

GITHUB_SHA_ENV_VAR_NAME = 'GITHUB_SHA'
COILSNAKE_GIT_COMMIT_PY_PATH = 'coilsnake/ui/git_commit.py'

def get_git_commit():
    # Try looking at the GitHub variable
    revision = os.environ.get(GITHUB_SHA_ENV_VAR_NAME)
    # If it wasn't set, run against head
    if not revision:
        revision = "HEAD"
    # Try to run git rev-parse to get the short hash
    try:
        print('Getting short hash for Git revision:', revision)
        git_commit = subprocess.check_output(['git', 'rev-parse', '--short', revision])
        return git_commit.strip().decode()
    except Exception as e:
        print('Error when running rev-parse:', e, sep='\n')
    # In case of error, return None
    return None

def write_git_commit(git_commit):
    # Force git_commit to be a value, or None
    git_commit = git_commit or None
    git_commit_file_text = f'GIT_COMMIT = {git_commit!r}'
    print(f"Writing '{COILSNAKE_GIT_COMMIT_PY_PATH}' with: {git_commit_file_text}")
    with open(COILSNAKE_GIT_COMMIT_PY_PATH, 'w') as f:
        print(git_commit_file_text, file=f)

if __name__ == '__main__':
    git_commit = get_git_commit()
    print('Found Git commit short hash:', git_commit)
    if '--write' in sys.argv[1:]:
        write_git_commit(git_commit)
