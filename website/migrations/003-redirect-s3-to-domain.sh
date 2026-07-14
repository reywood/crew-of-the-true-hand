#!/usr/bin/env bash
#
# 003-redirect-s3-to-domain.sh
#
# Make the raw S3 *website* endpoint 301-redirect to https://crewofthetruehand.com
# (path preserved), so bookmarks / search-indexed S3 URLs land on the canonical
# domain instead of serving a bare, unbranded copy of the site.
#
# ---------------------------------------------------------------------------
# WHY THIS TAKES TWO STEPS (and why order matters)
#
# After 002, CloudFront's origin was the S3 *website* endpoint. A redirect can
# only be configured on that same website endpoint — but S3 can't tell a direct
# visitor apart from CloudFront (both arrive with the same Host header), so
# turning on "redirect all requests" there would bounce CloudFront's OWN origin
# fetches too => infinite loop, taking down the live site.
#
# The fix, in order:
#   1. Repoint CloudFront at the S3 *REST* endpoint (crew-of-the-true-hand
#      .s3.us-east-1.amazonaws.com), which serves objects and IGNORES website
#      redirect rules. Add 403/404 -> /index.html error responses to preserve
#      the website endpoint's ErrorDocument behavior. WAIT for Deployed.
#   2. Only then set the bucket website config to RedirectAllRequestsTo the
#      domain. Now the website endpoint does nothing but redirect; CloudFront
#      no longer touches it, so there is no loop.
#
# Safe because the generated site is entirely flat *.html files (no reliance on
# S3 subdirectory index-document resolution); the REST endpoint + CloudFront
# DefaultRootObject=index.html cover the root.
# ---------------------------------------------------------------------------
#
# Idempotent: re-running detects the REST origin / redirect config already in
# place and skips the corresponding step.
#
# Prerequisites:
#   - 002-cloudfront-dns-ssl.sh has been run (distribution + domain exist)
#   - aws CLI perms: cloudfront:GetDistributionConfig, cloudfront:UpdateDistribution,
#     cloudfront:GetDistribution, s3:PutBucketWebsite, s3:GetBucketWebsite
#
set -euo pipefail

# ---- variables -----------------------------------------------------------
DOMAIN="${DOMAIN:-crewofthetruehand.com}"
BUCKET="${BUCKET:-crew-of-the-true-hand}"
REGION="us-east-1"
REST_ENDPOINT="${BUCKET}.s3.${REGION}.amazonaws.com"

TMPDIR="$(mktemp -d -t "${BUCKET}-redir.XXXXXX")"
trap 'rm -rf "${TMPDIR}"' EXIT

echo "==> Domain:   ${DOMAIN}"
echo "==> Bucket:   ${BUCKET}"
echo "==> REST:     ${REST_ENDPOINT}"
echo

# ---- 1. locate the distribution ------------------------------------------
echo "==> 1/4 Locating CloudFront distribution for ${DOMAIN}"
DIST_ID="$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Aliases.Items && contains(Aliases.Items, '${DOMAIN}')].Id | [0]" \
  --output text)"
if [ -z "${DIST_ID}" ] || [ "${DIST_ID}" = "None" ]; then
  echo "ERROR: no distribution aliased to ${DOMAIN}. Run 002 first." >&2
  exit 1
fi
echo "    Distribution: ${DIST_ID}"

# ---- 2. repoint origin to the REST endpoint (+ error responses) ----------
echo "==> 2/4 Ensuring CloudFront origin = REST endpoint"
aws cloudfront get-distribution-config --id "${DIST_ID}" --output json > "${TMPDIR}/dist.json"
ETAG="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["ETag"])' "${TMPDIR}/dist.json")"
CUR_ORIGIN="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["DistributionConfig"]["Origins"]["Items"][0]["DomainName"])' "${TMPDIR}/dist.json")"

if [ "${CUR_ORIGIN}" = "${REST_ENDPOINT}" ]; then
  echo "    Already on REST endpoint; skipping distribution update."
else
  echo "    Currently: ${CUR_ORIGIN} -> switching to ${REST_ENDPOINT}"
  REST_ENDPOINT="${REST_ENDPOINT}" python3 - "${TMPDIR}/dist.json" "${TMPDIR}/dist-new.json" <<'PY'
import json, os, sys
d = json.load(open(sys.argv[1]))
cfg = d["DistributionConfig"]
o = cfg["Origins"]["Items"][0]
o["DomainName"] = os.environ["REST_ENDPOINT"]
o["CustomOriginConfig"]["OriginProtocolPolicy"] = "https-only"
o["CustomOriginConfig"]["OriginSslProtocols"] = {"Quantity": 1, "Items": ["TLSv1.2"]}
# Preserve the website endpoint's "serve index.html for unknown paths" behavior.
cfg["CustomErrorResponses"] = {
    "Quantity": 2,
    "Items": [
        {"ErrorCode": 403, "ResponsePagePath": "/index.html", "ResponseCode": "404", "ErrorCachingMinTTL": 10},
        {"ErrorCode": 404, "ResponsePagePath": "/index.html", "ResponseCode": "404", "ErrorCachingMinTTL": 10},
    ],
}
json.dump(cfg, open(sys.argv[2], "w"))
PY
  aws cloudfront update-distribution --id "${DIST_ID}" \
    --distribution-config "file://${TMPDIR}/dist-new.json" \
    --if-match "${ETAG}" >/dev/null
  echo "    Update applied."
fi

# ---- 3. wait for the distribution to finish deploying --------------------
# MUST be Deployed on every edge before flipping the bucket, or in-flight edges
# still using the website endpoint as origin would loop.
echo "==> 3/4 Waiting for distribution to reach Deployed"
aws cloudfront wait distribution-deployed --id "${DIST_ID}"
echo "    Deployed."

# ---- 4. flip the bucket website config to redirect-all -------------------
echo "==> 4/4 Setting bucket website config to redirect -> https://${DOMAIN}"
aws s3api put-bucket-website --bucket "${BUCKET}" --website-configuration "{
  \"RedirectAllRequestsTo\": { \"HostName\": \"${DOMAIN}\", \"Protocol\": \"https\" }
}"
echo "    Applied."

# ---- verify ---------------------------------------------------------------
echo
echo "Verifying..."
WEBSITE_ENDPOINT="${BUCKET}.s3-website-${REGION}.amazonaws.com"
curl -sS -o /dev/null -w "  S3 website /sessions.html : %{http_code} -> %{redirect_url}\n" \
  "http://${WEBSITE_ENDPOINT}/sessions.html" || true
CF_IP="$(dig +short "$(aws cloudfront get-distribution --id "${DIST_ID}" --query 'Distribution.DomainName' --output text)" @1.1.1.1 | head -1)"
if [ -n "${CF_IP}" ]; then
  curl -sS -o /dev/null -w "  canonical site (home)     : %{http_code}\n" \
    --resolve "${DOMAIN}:443:${CF_IP}" "https://${DOMAIN}/" || true
fi
echo
echo "Done. Raw S3 website URLs now 301 to https://${DOMAIN} with the path preserved."
