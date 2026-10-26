#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8080/api/v1}"
TRIAGE_BASE_URL="${TRIAGE_BASE_URL:-http://localhost:8001}"
RAG_BASE_URL="${RAG_BASE_URL:-http://localhost:8003}"
ITERATIONS="${LOAD_SMOKE_ITERATIONS:-3}"
ATTEMPTS="${LOAD_SMOKE_ATTEMPTS:-30}"
DELAY_SECONDS="${LOAD_SMOKE_DELAY_SECONDS:-2}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

request() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  local token="${4:-}"
  local output="$TMP_DIR/response.json"
  local headers=(-H "Content-Type: application/json")
  if [ -n "$token" ]; then
    headers+=(-H "Authorization: Bearer $token")
  fi

  local status
  if [ -n "$body" ]; then
    status="$(curl -sS -o "$output" -w "%{http_code}" -X "$method" "${headers[@]}" -d "$body" "$url")"
  else
    status="$(curl -sS -o "$output" -w "%{http_code}" -X "$method" "${headers[@]}" "$url")"
  fi

  if [[ "$status" != 2* ]]; then
    echo "Request failed: $method $url returned $status" >&2
    cat "$output" >&2
    exit 1
  fi
  cat "$output"
}

json_field() {
  local field="$1"
  python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$field"
}

wait_for() {
  local name="$1"
  local url="$2"
  for attempt in $(seq 1 "$ATTEMPTS"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name is reachable."
      return 0
    fi
    echo "Waiting for $name ($attempt/$ATTEMPTS): $url"
    sleep "$DELAY_SECONDS"
  done
  echo "$name did not become reachable: $url" >&2
  exit 1
}

wait_for "backend api" "$API_BASE_URL/health"
wait_for "triage service" "$TRIAGE_BASE_URL/health"
wait_for "rag service" "$RAG_BASE_URL/health"

TOKEN="$(request POST "$API_BASE_URL/auth/dev-token" '{"subject":"load-smoke-adjuster","roles":["ADJUSTER"]}' | json_field token)"

for i in $(seq 1 "$ITERATIONS"); do
  suffix="$(date +%s)-$i"
  customer_number="CUST-SMOKE-$suffix"
  policy_number="POL-SMOKE-$suffix"

  request POST "$API_BASE_URL/customers" "{
    \"customerNumber\":\"$customer_number\",
    \"firstName\":\"Smoke\",
    \"lastName\":\"Tester\",
    \"email\":\"smoke-$suffix@example.test\",
    \"country\":\"US\"
  }" "$TOKEN" >/dev/null

  request POST "$API_BASE_URL/policies" "{
    \"customerNumber\":\"$customer_number\",
    \"policyNumber\":\"$policy_number\",
    \"policyType\":\"PERSONAL_AUTO\",
    \"effectiveDate\":\"2026-01-01\",
    \"expirationDate\":\"2027-01-01\",
    \"premiumAmount\":1400.00,
    \"currency\":\"USD\"
  }" "$TOKEN" >/dev/null

  request POST "$API_BASE_URL/policies/$policy_number/coverages" '{
    "coverageCode":"COLLISION",
    "coverageName":"Collision Coverage",
    "coverageType":"COLLISION",
    "limitAmount":25000.00,
    "deductibleAmount":500.00,
    "effectiveDate":"2026-01-01",
    "expirationDate":"2027-01-01",
    "exclusions":"[]"
  }' "$TOKEN" >/dev/null

  request POST "$API_BASE_URL/policies/$policy_number/activate" '{}' "$TOKEN" >/dev/null

  claim_response="$(request POST "$API_BASE_URL/claims/fnol" "{
    \"policyNumber\":\"$policy_number\",
    \"claimType\":\"AUTO_COLLISION\",
    \"lossDate\":\"2026-06-24\",
    \"reportedAt\":\"2026-06-25T10:15:30Z\",
    \"lossLocation\":\"Columbus, OH\",
    \"description\":\"Low-speed collision smoke test.\",
    \"estimatedLossAmount\":9000.00
  }" "$TOKEN")"
  claim_number="$(printf "%s" "$claim_response" | json_field claimNumber)"
  request GET "$API_BASE_URL/claims/$claim_number" "" "$TOKEN" >/dev/null

  request POST "$TRIAGE_BASE_URL/ai/v1/triage/score" "{
    \"claimId\":\"$claim_number\",
    \"claimNumber\":\"$claim_number\",
    \"policyFeatures\":{
      \"policyType\":\"PERSONAL_AUTO\",
      \"policyAgeDays\":180,
      \"coverageLimitAmount\":25000.0,
      \"deductibleAmount\":500.0,
      \"coverageValid\":true,
      \"coverageReasons\":[]
    },
    \"claimFeatures\":{
      \"claimType\":\"AUTO_COLLISION\",
      \"estimatedLossAmount\":9000.0,
      \"injuryReported\":false,
      \"thirdPartyInvolved\":false,
      \"policeReportAvailable\":true,
      \"lossReportDelayDays\":1,
      \"priorClaimsCount\":0
    },
    \"textFeatures\":{\"lossDescription\":\"Low-speed collision smoke test.\"}
  }" >/dev/null

  request POST "$RAG_BASE_URL/ai/v1/rag/ingest" "{
    \"documentId\":\"DOC-SMOKE-$suffix\",
    \"claimId\":\"$claim_number\",
    \"policyId\":\"$policy_number\",
    \"documentType\":\"POLICY_DOCUMENT\",
    \"title\":\"Smoke Test Policy\",
    \"text\":\"Collision Coverage\nCollision damage is covered when the policy is active on the loss date.\",
    \"metadata\":{\"sourceSystem\":\"load-smoke\"}
  }" >/dev/null

  request POST "$RAG_BASE_URL/ai/v1/rag/query" "{
    \"claimId\":\"$claim_number\",
    \"question\":\"Is collision damage covered?\",
    \"topK\":3
  }" >/dev/null

  echo "Completed load smoke iteration $i for $claim_number."
done

echo "Load smoke checks passed."
