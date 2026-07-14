#!/usr/bin/env bash
#
# 002-cloudfront-dns-ssl.sh
#
# Front the S3 website bucket (from 001) with a CloudFront distribution, put an
# ACM SSL certificate on it, and point the Route 53 domain crewofthetruehand.com
# (apex + www) at the distribution.
#
# This is the "HTTPS + custom domain" follow-up that 001 leaves off at. It is
# idempotent and safe to re-run: existing zone / cert / distribution are reused
# rather than duplicated, and every DNS write is an UPSERT.
#
# ---------------------------------------------------------------------------
# THE NAMESERVER GATE
#
# ACM validates the certificate over DNS, which only works once Route 53 is the
# authoritative nameserver for the domain. If this script has to CREATE the
# hosted zone (first run), it sets everything up, prints the zone's four NS
# records, and STOPS — because cert validation cannot succeed until you point
# the domain's nameservers at those four values *at your registrar*. Do that,
# give it a few minutes to propagate, then re-run this same script to finish
# (cert wait -> CloudFront -> alias records). On the second run the zone already
# exists, so it sails past the gate.
#
# If the domain is not registered anywhere yet, register it first (Route 53
# Domains or any registrar), then run this.
# ---------------------------------------------------------------------------
#
# Prerequisites:
#   - 001-create-s3-bucket.sh has been run (bucket exists with website hosting)
#   - aws CLI configured with Route 53 + ACM + CloudFront permissions
#
set -euo pipefail

# ---- variables -----------------------------------------------------------
DOMAIN="${DOMAIN:-crewofthetruehand.com}"
WWW="www.${DOMAIN}"
BUCKET="${BUCKET:-crew-of-the-true-hand}"
# The bucket lives in us-east-1 and ACM certs for CloudFront MUST be in us-east-1.
REGION="us-east-1"
# S3 *website* endpoint (dash form for us-east-1) — used as a custom origin so
# CloudFront inherits the bucket's index-document / error-document routing.
S3_WEBSITE_ENDPOINT="${BUCKET}.s3-website-${REGION}.amazonaws.com"
# Constant hosted-zone id for ALL CloudFront distributions (AWS-published).
CLOUDFRONT_ZONE_ID="Z2FDTNDATAQYW2"
# AWS managed cache policy "CachingOptimized".
CACHE_POLICY_ID="658327ea-f89d-4fab-a63d-7e88639e58f6"

TMPDIR="$(mktemp -d -t "${BUCKET}-cf.XXXXXX")"
trap 'rm -rf "${TMPDIR}"' EXIT

echo "==> Domain:   ${DOMAIN} (+ ${WWW})"
echo "==> Bucket:   ${BUCKET}"
echo "==> Origin:   ${S3_WEBSITE_ENDPOINT}"
echo

# ---- 1. hosted zone -------------------------------------------------------
echo "==> 1/7 Resolving Route 53 hosted zone"
HOSTED_ZONE_ID="$(aws route53 list-hosted-zones-by-name --dns-name "${DOMAIN}" \
  --query "HostedZones[?Name=='${DOMAIN}.'].Id | [0]" --output text)"

ZONE_WAS_CREATED=false
if [ -z "${HOSTED_ZONE_ID}" ] || [ "${HOSTED_ZONE_ID}" = "None" ]; then
  echo "    No hosted zone for ${DOMAIN}; creating one."
  HOSTED_ZONE_ID="$(aws route53 create-hosted-zone \
    --name "${DOMAIN}" \
    --caller-reference "${DOMAIN}-$(date +%s)" \
    --hosted-zone-config Comment="Crew of the True Hand" \
    --query 'HostedZone.Id' --output text)"
  ZONE_WAS_CREATED=true
fi
HOSTED_ZONE_ID="${HOSTED_ZONE_ID#/hostedzone/}"
echo "    Hosted zone: ${HOSTED_ZONE_ID}"

# ---- 2. ACM certificate (request or reuse) --------------------------------
echo "==> 2/7 Resolving ACM certificate"
CERT_ARN="$(aws acm list-certificates --region "${REGION}" \
  --query "CertificateSummaryList[?DomainName=='${DOMAIN}'].CertificateArn | [0]" \
  --output text)"

if [ -z "${CERT_ARN}" ] || [ "${CERT_ARN}" = "None" ]; then
  echo "    Requesting new certificate for ${DOMAIN} + ${WWW}"
  CERT_ARN="$(aws acm request-certificate --region "${REGION}" \
    --domain-name "${DOMAIN}" \
    --subject-alternative-names "${WWW}" \
    --validation-method DNS \
    --query CertificateArn --output text)"
fi
echo "    Certificate: ${CERT_ARN}"

# ---- 3. DNS validation records -------------------------------------------
# The ResourceRecord fields are populated asynchronously after request; poll.
echo "==> 3/7 Writing ACM DNS validation records into the zone"
for _ in $(seq 1 12); do
  VOPTS="$(aws acm describe-certificate --certificate-arn "${CERT_ARN}" --region "${REGION}" \
    --query 'Certificate.DomainValidationOptions' --output json)"
  if printf '%s' "${VOPTS}" | python3 -c \
      'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d and all("ResourceRecord" in o for o in d) else 1)'; then
    break
  fi
  sleep 5
done

printf '%s' "${VOPTS}" | python3 -c '
import json, sys
opts = json.load(sys.stdin)
seen, changes = set(), []
for o in opts:
    rr = o.get("ResourceRecord")
    if not rr:
        continue
    key = (rr["Name"], rr["Type"])
    if key in seen:            # apex + www often share one validation record
        continue
    seen.add(key)
    changes.append({
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": rr["Name"], "Type": rr["Type"], "TTL": 300,
            "ResourceRecords": [{"Value": rr["Value"]}],
        },
    })
json.dump({"Comment": "ACM DNS validation", "Changes": changes}, sys.stdout)
' > "${TMPDIR}/validation.json"

aws route53 change-resource-record-sets --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --change-batch "file://${TMPDIR}/validation.json" >/dev/null
echo "    Validation records written."

# ---- the nameserver gate --------------------------------------------------
if [ "${ZONE_WAS_CREATED}" = true ]; then
  echo
  echo "======================================================================"
  echo " ACTION REQUIRED — delegate the domain to Route 53, then re-run."
  echo
  echo " Set these four nameservers for ${DOMAIN} at your registrar:"
  aws route53 get-hosted-zone --id "${HOSTED_ZONE_ID}" \
    --query 'DelegationSet.NameServers' --output text | tr '\t' '\n' | sed 's/^/     - /'
  echo
  echo " The certificate and its validation records are already in place; ACM"
  echo " will validate automatically once delegation propagates (minutes to a"
  echo " couple of hours). Then run this script again to create CloudFront and"
  echo " point the domain at it:"
  echo
  echo "     ./website/migrations/002-cloudfront-dns-ssl.sh"
  echo "======================================================================"
  exit 0
fi

# ---- 4. wait for certificate validation ----------------------------------
echo "==> 4/7 Waiting for certificate validation (needs NS delegation live)"
echo "    If this times out, the domain's nameservers aren't pointed at zone"
echo "    ${HOSTED_ZONE_ID} yet. Fix that at the registrar and re-run."
aws acm wait certificate-validated --certificate-arn "${CERT_ARN}" --region "${REGION}"
echo "    Certificate ISSUED."

# ---- 5. CloudFront distribution (create or reuse) -------------------------
echo "==> 5/7 Resolving CloudFront distribution"
DIST_ID="$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Aliases.Items && contains(Aliases.Items, '${DOMAIN}')].Id | [0]" \
  --output text)"

if [ -z "${DIST_ID}" ] || [ "${DIST_ID}" = "None" ]; then
  echo "    Creating distribution."
  cat > "${TMPDIR}/cf.json" <<EOF
{
  "CallerReference": "${DOMAIN}-$(date +%s)",
  "Comment": "Crew of the True Hand static site",
  "Enabled": true,
  "PriceClass": "PriceClass_100",
  "HttpVersion": "http2and3",
  "DefaultRootObject": "index.html",
  "Aliases": { "Quantity": 2, "Items": ["${DOMAIN}", "${WWW}"] },
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "s3-website-origin",
      "DomainName": "${S3_WEBSITE_ENDPOINT}",
      "OriginPath": "",
      "CustomHeaders": { "Quantity": 0 },
      "CustomOriginConfig": {
        "HTTPPort": 80,
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "http-only",
        "OriginSslProtocols": { "Quantity": 1, "Items": ["TLSv1.2"] },
        "OriginReadTimeout": 30,
        "OriginKeepaliveTimeout": 5
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-website-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "Compress": true,
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"] }
    },
    "CachePolicyId": "${CACHE_POLICY_ID}"
  },
  "ViewerCertificate": {
    "ACMCertificateArn": "${CERT_ARN}",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  }
}
EOF
  DIST_JSON="$(aws cloudfront create-distribution --distribution-config "file://${TMPDIR}/cf.json")"
  DIST_ID="$(printf '%s' "${DIST_JSON}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["Distribution"]["Id"])')"
fi

DIST_DOMAIN="$(aws cloudfront get-distribution --id "${DIST_ID}" \
  --query 'Distribution.DomainName' --output text)"
echo "    Distribution: ${DIST_ID} (${DIST_DOMAIN})"

# ---- 6. point apex + www at CloudFront ------------------------------------
echo "==> 6/7 Aliasing ${DOMAIN} and ${WWW} to CloudFront"
cat > "${TMPDIR}/alias.json" <<EOF
{
  "Comment": "Point apex + www at CloudFront",
  "Changes": [
    { "Action": "UPSERT", "ResourceRecordSet": { "Name": "${DOMAIN}", "Type": "A",
      "AliasTarget": { "HostedZoneId": "${CLOUDFRONT_ZONE_ID}", "DNSName": "${DIST_DOMAIN}", "EvaluateTargetHealth": false } } },
    { "Action": "UPSERT", "ResourceRecordSet": { "Name": "${DOMAIN}", "Type": "AAAA",
      "AliasTarget": { "HostedZoneId": "${CLOUDFRONT_ZONE_ID}", "DNSName": "${DIST_DOMAIN}", "EvaluateTargetHealth": false } } },
    { "Action": "UPSERT", "ResourceRecordSet": { "Name": "${WWW}", "Type": "A",
      "AliasTarget": { "HostedZoneId": "${CLOUDFRONT_ZONE_ID}", "DNSName": "${DIST_DOMAIN}", "EvaluateTargetHealth": false } } },
    { "Action": "UPSERT", "ResourceRecordSet": { "Name": "${WWW}", "Type": "AAAA",
      "AliasTarget": { "HostedZoneId": "${CLOUDFRONT_ZONE_ID}", "DNSName": "${DIST_DOMAIN}", "EvaluateTargetHealth": false } } }
  ]
}
EOF
aws route53 change-resource-record-sets --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --change-batch "file://${TMPDIR}/alias.json" >/dev/null
echo "    Alias records written."

# ---- 7. done --------------------------------------------------------------
echo "==> 7/7 Done"
echo
echo "  https://${DOMAIN}  and  https://${WWW}  ->  CloudFront ${DIST_ID}"
echo
echo "  CloudFront takes ~15 min to finish deploying the new distribution."
echo "  Content still comes from s3://${BUCKET}/ — keep deploying with"
echo "  ./website/bin/deploy.sh (add a CloudFront invalidation if you want"
echo "  edits to appear before cached objects expire):"
echo
echo "     aws cloudfront create-invalidation --distribution-id ${DIST_ID} --paths '/*'"
