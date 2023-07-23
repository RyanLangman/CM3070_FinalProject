#!/bin/bash

CLIENT_ID="1234"
CLIENT_SECRET="5678"
API_URL="http://localhost:8000/token"

TOKEN=$(curl -X POST -H "Content-Type: application/json" \
  -d "{\"client_id\": \"${CLIENT_ID}\", \"client_secret\": \"${CLIENT_SECRET}\"}" \
  ${API_URL} | jq -r '.access_token')

echo "Access Token: ${TOKEN}"


API_URL="http://localhost:8000/dream"

curl -X POST -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
  -d '{"dream_description": "My dream description"}' \
  ${API_URL}
