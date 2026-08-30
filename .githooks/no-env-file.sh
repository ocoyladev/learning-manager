#!/usr/bin/env bash
set -eu

while IFS= read -r -d '' path; do
    if [ "${path##*/}" = ".env" ]; then
        printf 'ERROR: staged .env files are not allowed\n' >&2
        exit 1
    fi
done < <(git diff --cached --name-only --diff-filter=ACMR -z)
