#!/bin/bash
source userpass
curl --url "http://127.0.0.1:7783" --data "{
  \"userpass\": \"$userpass\",
  \"method\": \"electrum\",
  \"coin\": \"JKC\",
  \"servers\": [
    { \"url\": \"electrum.junkiewally.xyz:50003\" },
    { \"url\": \"electrum.junkiewally.xyz:50004\", \"ssl\": true },
    { \"url\": \"electrum.junkiewally.xyz:50005\", \"wss\": true }
  ]
}"
