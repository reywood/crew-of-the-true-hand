#!/usr/bin/env bash
#
# 001-create-s3-bucket.sh
#
# Provision an S3 bucket configured for public static website hosting and
# upload the generated site. Idempotent-ish — safe to re-run, but step 1 will
# fail with BucketAlreadyOwnedByYou if the bucket already exists (which is
# fine; the later steps will still apply).
#
# Prerequisites:
#   - aws CLI installed and configured (`aws configure`)
#   - python3 website/generate.py has been run so website/site/ is up to date
#
# To deploy updates after the first run, just re-run step 5 (the `aws s3 sync`).
#
set -euo pipefail

# ---- variables -----------------------------------------------------------
BUCKET="${BUCKET:-crew-of-the-true-hand}"
REGION="${REGION:-us-east-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="${SITE_DIR:-${SCRIPT_DIR}/../site}"
POLICY_FILE="$(mktemp -t "${BUCKET}-policy.XXXXXX.json")"
trap 'rm -f "${POLICY_FILE}"' EXIT

echo "==> Bucket:  ${BUCKET}"
echo "==> Region:  ${REGION}"
echo "==> Source:  ${SITE_DIR}"

# ---- 1. create the bucket -------------------------------------------------
# us-east-1 is special: it must NOT have --create-bucket-configuration.
# Any other region requires --create-bucket-configuration LocationConstraint=...
echo "==> 1/5 Creating bucket"
if [ "$REGION" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
else
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"
fi

# ---- 2. allow public access on this bucket --------------------------------
# Newly created buckets block public access by default; turn that off so the
# bucket policy below can take effect.
echo "==> 2/5 Disabling public-access block"
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# ---- 3. attach a public-read bucket policy --------------------------------
echo "==> 3/5 Applying public-read bucket policy"
cat > "${POLICY_FILE}" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::${BUCKET}/*"
  }]
}
EOF
aws s3api put-bucket-policy --bucket "$BUCKET" \
  --policy "file://${POLICY_FILE}"

# ---- 4. enable static website hosting -------------------------------------
echo "==> 4/5 Enabling static website hosting"
aws s3 website "s3://${BUCKET}/" \
  --index-document index.html \
  --error-document index.html

# ---- 5. upload the generated site -----------------------------------------
echo "==> 5/5 Syncing ${SITE_DIR} to s3://${BUCKET}/"
if [ ! -d "${SITE_DIR}" ]; then
  echo "ERROR: ${SITE_DIR} does not exist. Run 'python3 website/generate.py' first." >&2
  exit 1
fi
aws s3 sync "${SITE_DIR}" "s3://${BUCKET}/" --delete

# ---- done ----------------------------------------------------------------
if [ "$REGION" = "us-east-1" ]; then
  URL="http://${BUCKET}.s3-website-${REGION}.amazonaws.com"
else
  URL="http://${BUCKET}.s3-website.${REGION}.amazonaws.com"
fi
echo
echo "Done. Site URL: ${URL}"
echo "(HTTP only. For HTTPS + custom domain, front the bucket with CloudFront.)"
