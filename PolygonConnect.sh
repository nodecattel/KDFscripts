#!/bin/bash
source userpass
curl --url "http://127.0.0.1:7783" --data "{
  \"userpass\": \"$userpass\",
  \"method\": \"enable_eth_with_tokens\",
  \"mmrpc\": \"2.0\",
  \"params\": {
    \"ticker\": \"MATIC\",
    \"mm2\": 1,
    \"swap_contract_address\": \"0x9130b257D37A52E52F21054c4DA3450c72f595CE\",
    \"fallback_swap_contract\": \"0x9130b257D37A52E52F21054c4DA3450c72f595CE\",
    \"swap_v2_contracts\": {
      \"maker_swap_v2_contract\": \"0x9130b257D37A52E52F21054c4DA3450c72f595CE\",
      \"taker_swap_v2_contract\": \"0x9130b257D37A52E52F21054c4DA3450c72f595CE\",
      \"nft_maker_swap_v2_contract\": \"0x9130b257D37A52E52F21054c4DA3450c72f595CE\"
    },
    \"nodes\": [
      {
        \"url\": \"https://node.komodo.earth:8080/polygon\",
        \"komodo_proxy\": true
      },
      {
        \"url\": \"https://polygon.drpc.org\",
        \"ws_url\": \"wss://polygon.drpc.org\"
      },
      {
        \"url\": \"https://polygon.gateway.tenderly.co\",
        \"ws_url\": \"wss://polygon.gateway.tenderly.co\"
      },
      {
        \"url\": \"https://block-proxy.komodo.earth/rpc/matic\",
        \"ws_url\": \"wss://block-proxy.komodo.earth/rpc/matic/websocket\"
      },
      {
        \"url\": \"https://electrum3.cipig.net:18755\",
        \"ws_url\": \"wss://electrum3.cipig.net:38755\"
      },
      {
        \"url\": \"https://polygon-bor-rpc.publicnode.com\",
        \"ws_url\": \"wss://polygon-bor-rpc.publicnode.com\"
      }
    ],
    \"tx_history\": true,
    \"erc20_tokens_requests\": [
      {
        \"ticker\": \"USDT-PLG20\",
        \"required_confirmations\": 4
      }
    ],
    \"required_confirmations\": 5,
    \"requires_notarization\": false,
    \"priv_key_policy\": \"ContextPrivKey\"
  }
}"
