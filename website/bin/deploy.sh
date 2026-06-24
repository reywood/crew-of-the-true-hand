#!/usr/bin/env bash

BUCKET="${BUCKET:-crew-of-the-true-hand}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="${SITE_DIR:-${SCRIPT_DIR}/../site}"

aws s3 sync "${SITE_DIR}" "s3://${BUCKET}/" --delete
