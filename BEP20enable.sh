#!/bin/bash
source userpass

# Replace USDT-BEP20 with any other BEP20 token you want to enable
TOKEN_TICKER="USDT-BEP20"

curl --url "http://127.0.0.1:7783" --data "{
  \"userpass\": \"$userpass\",
  \"method\": \"enable_erc20\",
  \"mmrpc\": \"2.0\",
  \"params\": {
    \"ticker\": \"$TOKEN_TICKER\",
    \"activation_params\": {
      \"required_confirmations\": 4
    }
  }
}"
