# KDFscripts

This repository contains a collection of Bash scripts and a Python CLI (`dex.py`) to help you interact with and manage the [Komodo DeFi Framework (KDF)](https://github.com/KomodoPlatform/komodo-defi-framework).

## 📂 Placement

To work correctly, all scripts in this repository should be placed in the same directory as the compiled `kdf` binary:

```
~/komodo-defi-framework/target/debug/
```

or

```
~/komodo-defi-framework/target/release/
```

If you haven't installed or built KDF yet, follow the instructions at:  
👉 https://github.com/KomodoPlatform/komodo-defi-framework

---

## 🧠 What This Repo Includes

| Script | Description |
|--------|-------------|
| `BNBConnect.sh` | Connects to BNB Chain and initializes token support |
| `PolygonConnect.sh` | Connects to Polygon (MATIC) network |
| `KMDconnect.sh` | Connects to Komodo network using Electrum |
| `JKCConnect.sh` | Connects to Junkcoin network (custom Electrum setup) |
| `LTCconnect.sh` | Connects to Litecoin network |
| `BEP20enable.sh`, `PLG20enable.sh` | Enables BEP20 or Polygon tokens for trading |
| `start.sh` / `stop.sh` | Starts or stops the `kdf` daemon |
| `mybalance.sh` / `myorders.sh` / `order_status.sh` | Gets balance, current orders, and status info |
| `orderbook.sh` | Views live orderbook of a trading pair |
| `place_order.sh` / `cancel_order.sh` | Places or cancels a trade |
| `withdraw.sh` | Withdraws coins to external address |
| `sendrawtransaction.sh` | Broadcasts raw transaction |
| `show_priv_key.sh` | Shows private key (⚠️ for advanced users only) |
| `dex.py` | Interactive Python3 terminal for managing coins, orders, balances, portfolio tracking, and more |

---

## ✅ Setup Instructions

### 1. Make all scripts executable

```bash
chmod +x BEP20enable.sh BNBConnect.sh cancel_order.sh dex.py JKCConnect.sh KMDconnect.sh LTCconnect.sh mybalance.sh myorders.sh orderbook.sh order_status.sh place_order.sh PLG20enable.sh PolygonConnect.sh sendrawtransaction.sh show_priv_key.sh start.sh stop.sh withdraw.sh
```

### 2. Copy all scripts into the KDF directory

```bash
cp BEP20enable.sh BNBConnect.sh cancel_order.sh dex.py JKCConnect.sh KMDconnect.sh LTCconnect.sh mybalance.sh myorders.sh orderbook.sh order_status.sh place_order.sh PLG20enable.sh PolygonConnect.sh sendrawtransaction.sh show_priv_key.sh start.sh stop.sh withdraw.sh ~/komodo-defi-framework/target/debug/
```

> Or replace `debug/` with `release/` if you're using the release build.

---

## 🚀 Getting Started with `dex.py`

```bash
cd ~/komodo-defi-framework/target/debug
python3 dex.py
```

This CLI offers:
- Coin connection and management
- Balance and portfolio summary (with USD valuation)
- Trading (set price, cancel orders, check orderbook)
- Visualizations (requires `matplotlib`)
- Price tracking via CoinGecko API

If required Python packages are missing, the script will prompt you to install them automatically:
```bash
pip install requests matplotlib numpy tabulate colorama
```

---

## 💡 Tips

- Make sure `userpass` is present in the same directory as `kdf` and scripts.
- You can run each `.sh` script directly or rely on `dex.py` to perform tasks interactively.
- For portfolio and order visualizations, make sure you have `matplotlib` installed.

---

## 🛠 Contributing

Feel free to submit PRs for:
- New chain integrations
- Bug fixes or enhancements to `dex.py`
- Script automation improvements

---


**License:** MIT  
**Author:** @nodecattel
