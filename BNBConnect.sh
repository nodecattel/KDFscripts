#!/bin/bash
source userpass
curl --url "http://127.0.0.1:7783" --data "{
  \"userpass\": \"$userpass\",
  \"method\": \"enable_eth_with_tokens\",
  \"mmrpc\": \"2.0\",
  \"params\": {
    \"ticker\": \"BNB\",
    \"mm2\": 1,
    \"swap_contract_address\": \"0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31\",
    \"fallback_swap_contract\": \"0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31\",
    \"swap_v2_contracts\": {
      \"maker_swap_v2_contract\": \"0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31\",
      \"taker_swap_v2_contract\": \"0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31\",
      \"nft_maker_swap_v2_contract\": \"0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31\"
    },
    \"nodes\": [
      {
        \"url\": \"https://bsc1.cipig.net:18655\",
        \"ws_url\": \"wss://bsc1.cipig.net:38655\"
      },
      {
        \"url\": \"https://bsc2.cipig.net:18655\",
        \"ws_url\": \"wss://bsc2.cipig.net:38655\"
      },
      {
        \"url\": \"https://bsc3.cipig.net:18655\",
        \"ws_url\": \"wss://bsc3.cipig.net:38655\"
      },
      {
        \"url\": \"https://bsc-rpc.publicnode.com\",
        \"ws_url\": \"wss://bsc-rpc.publicnode.com\"
      },
      {
        \"url\": \"https://block-proxy.komodo.earth/rpc/bnb\",
        \"ws_url\": \"wss://block-proxy.komodo.earth/rpc/bnb/websocket\"
      }
    ],
    \"tx_history\": true,
    \"erc20_tokens_requests\": [
      {
        \"ticker\": \"USDT-BEP20\",
        \"required_confirmations\": 4
      }
    ],
    \"required_confirmations\": 5,
    \"requires_notarization\": false,
    \"priv_key_policy\": \"ContextPrivKey\"
  }
}"
