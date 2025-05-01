#!/usr/bin/env python3

import os
import json
import subprocess
import time
import sys
import getpass
from pathlib import Path

# Function to check and install dependencies
def check_install_dependencies():
    required_packages = ['requests', 'matplotlib', 'numpy', 'tabulate', 'colorama']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        install = input("Would you like to install them now? (y/n): ")
        if install.lower() == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print("Dependencies installed successfully")
                # Force reload modules
                import importlib
                import sys
                for package in missing_packages:
                    if package in sys.modules:
                        importlib.reload(sys.modules[package])
                return True
            except Exception as e:
                print(f"Failed to install dependencies: {e}")
                print("Please install the following packages manually:")
                print(f"pip install {' '.join(missing_packages)}")
                return False
        else:
            print("Cannot continue without required dependencies")
            return False
    return True

# Check and install dependencies
if not check_install_dependencies():
    sys.exit(1)

# Now import the dependencies
import requests
try:
    import matplotlib.pyplot as plt
    import numpy as np
    from tabulate import tabulate
    from colorama import Fore, Style, init
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please install the required dependencies and try again")
    sys.exit(1)

# Initialize colorama
init(autoreset=True)

class KDFManager:
    def __init__(self):
        self.kdf_dir = os.path.expanduser("~/komodo-defi-framework/target/debug")
        self.userpass = None
        self.load_userpass()
        self.current_coin = None
        self.coins_enabled = set()
        self.default_coins = ["JKC", "BTC", "DOGE", "KMD", "FIRO"]
        self.coin_prices = {}
        self.last_price_update = 0
        self.coingecko_api_key = None
        self.load_coingecko_api_key()
        
        # Mapping from KDF coin tickers to CoinGecko IDs
        self.coingecko_ids = {
            "KMD": "komodo",
            "BTC": "bitcoin",
            "DOGE": "dogecoin",
            "FIRO": "zcoin",
            "JKC": "junkcoin",
            "LTC": "litecoin",
            "USDT": "tether",
            "BUSD": "binance-peg-busd",
            "DAI": "dai"
        }
        
        # Hardcoded electrum servers for better reliability
        self.coin_servers = {
            "JKC": [
                {"url": "electrum.junkiewally.xyz:50003"}
            ],
            "KMD": [
                {"url": "electrum.junkiewally.xyz:50003"},
                {"url": "electrum1.cipig.net:10001"},
                {"url": "electrum2.cipig.net:10001"},
                {"url": "electrum3.cipig.net:10001"}
            ],
            "BTC": [
                {"url": "electrum.junkiewally.xyz:50003"},
                {"url": "electrum1.cipig.net:10000"},
                {"url": "electrum2.cipig.net:10000"},
                {"url": "electrum3.cipig.net:10000"}
            ],
            "DOGE": [
                {"url": "electrum1.cipig.net:10060"},
                {"url": "electrum2.cipig.net:10060"},
                {"url": "electrum3.cipig.net:10060"}
            ],
            "LTC": [
                {"url": "electrum1.cipig.net:10063"},
                {"url": "electrum2.cipig.net:10063"},
                {"url": "electrum3.cipig.net:10063"}
            ],
            "FIRO": [
                {"url": "electrumx.firo.org:50001"},
                {"url": "electrumx01.firo.org:50001"},
                {"url": "electrumx02.firo.org:50001"},
                {"url": "electrumx03.firo.org:50001"}
            ]
        }
        
    def load_coingecko_api_key(self):
        """Load CoinGecko API key from file"""
        api_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coingecko-key")
        
        if os.path.exists(api_key_file):
            try:
                with open(api_key_file, 'r') as f:
                    self.coingecko_api_key = f.read().strip()
                    if self.coingecko_api_key:
                        print(f"{Fore.GREEN}CoinGecko API key loaded successfully{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Error loading CoinGecko API key: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No CoinGecko API key found. Using free API with rate limits.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}To use the Pro API, create a file named 'coingecko-key' in the same directory as this script with your API key.{Style.RESET_ALL}")
            
            # Create an empty file for future use
            try:
                with open(api_key_file, 'w') as f:
                    f.write("# Add your CoinGecko API key below (remove this line and add key)\n")
                print(f"{Fore.YELLOW}Created template file at {api_key_file}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Error creating API key template file: {e}{Style.RESET_ALL}")

    def load_userpass(self):
        """Load userpass from the userpass file"""
        userpass_file = os.path.join(self.kdf_dir, "userpass")
        try:
            with open(userpass_file, 'r') as f:
                content = f.read().strip()
                if content.startswith("userpass="):
                    self.userpass = content.split("=")[1]
                    print(f"{Fore.GREEN}Userpass loaded successfully{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Invalid userpass format{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}Userpass file not found at {userpass_file}{Style.RESET_ALL}")
            self.create_userpass()

    def create_userpass(self):
        """Create a new userpass file"""
        userpass = getpass.getpass("Enter your RPC password: ")
        userpass_file = os.path.join(self.kdf_dir, "userpass")
        with open(userpass_file, 'w') as f:
            f.write(f"userpass={userpass}")
        self.userpass = userpass
        print(f"{Fore.GREEN}Userpass file created successfully{Style.RESET_ALL}")

    def is_kdf_running(self):
        """Check if KDF is running"""
        try:
            response = self.send_request({"method": "version"})
            return response is not None
        except:
            return False

    def start_kdf(self):
        """Start the KDF daemon"""
        if self.is_kdf_running():
            print(f"{Fore.YELLOW}KDF is already running{Style.RESET_ALL}")
            return True

        start_script = os.path.join(self.kdf_dir, "start.sh")
        if not os.path.exists(start_script):
            print(f"{Fore.RED}start.sh script not found at {start_script}{Style.RESET_ALL}")
            # Try direct command
            try:
                cmd = f"cd {self.kdf_dir} && stdbuf -oL nohup ./kdf"
                subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"{Fore.GREEN}KDF daemon starting directly...{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error starting KDF daemon directly: {e}{Style.RESET_ALL}")
                return False

        else:
            try:
                # Run the start script
                subprocess.Popen(["bash", start_script], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
                print(f"{Fore.GREEN}KDF daemon starting...{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error starting KDF daemon: {e}{Style.RESET_ALL}")
                return False
                
        # Wait for KDF to start
        max_attempts = 10
        for i in range(max_attempts):
            time.sleep(2)  # Give it some time to start
            if self.is_kdf_running():
                print(f"{Fore.GREEN}KDF daemon started successfully{Style.RESET_ALL}")
                return True
            print(f"Waiting for KDF to start ({i+1}/{max_attempts})...")
        
        print(f"{Fore.RED}KDF daemon failed to start after {max_attempts} attempts{Style.RESET_ALL}")
        return False

    def stop_kdf(self):
        """Stop the KDF daemon"""
        if not self.is_kdf_running():
            print(f"{Fore.YELLOW}KDF is not running{Style.RESET_ALL}")
            return True

        try:
            response = self.send_request({"method": "stop", "userpass": self.userpass})
            if response and response.get("result") == "success":
                print(f"{Fore.GREEN}KDF daemon stopped successfully{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}Failed to stop KDF daemon: {response}{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}Error stopping KDF daemon: {e}{Style.RESET_ALL}")
            return False

    def send_request(self, payload):
        """Send a request to the KDF API"""
        # Ensure userpass is at the top level of the JSON
        if self.userpass and "userpass" not in payload:
            payload["userpass"] = self.userpass
        
        try:
            response = requests.post("http://127.0.0.1:7783", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        print(f"{Fore.RED}Error details: {error_json['error']}{Style.RESET_ALL}")
                except:
                    print(f"{Fore.RED}Could not decode error response{Style.RESET_ALL}")
                return None
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}Error: Could not connect to KDF API. Is KDF running?{Style.RESET_ALL}")
            return None
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Invalid JSON response from API{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}Error sending request: {e}{Style.RESET_ALL}")
            return None

    def detect_active_coins(self):
        """Detect which coins are already active in KDF"""
        print(f"{Fore.YELLOW}Detecting active coins...{Style.RESET_ALL}")
        
        # Common coins to check
        coins_to_check = ["BTC", "KMD", "LTC", "DOGE", "FIRO", "JKC"]
        
        for coin in coins_to_check:
            payload = {
                "userpass": self.userpass,
                "method": "my_balance",
                "coin": coin
            }
            
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post("http://127.0.0.1:7783", 
                                       data=json.dumps(payload), 
                                       headers=headers)
                
                if response.status_code == 200:
                    response_json = response.json()
                    if 'balance' in response_json:
                        self.coins_enabled.add(coin)
                        print(f"{Fore.GREEN}Detected active coin: {coin}{Style.RESET_ALL}")
            except:
                pass
        
        if self.coins_enabled:
            self.current_coin = list(self.coins_enabled)[0]
            print(f"{Fore.GREEN}Found {len(self.coins_enabled)} active coins: {', '.join(self.coins_enabled)}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No active coins detected{Style.RESET_ALL}")

    def load_electrum_servers(self, coin):
        """Load electrum servers from GitHub"""
        try:
            url = f"https://raw.githubusercontent.com/KomodoPlatform/coins/master/electrums/{coin}"
            response = requests.get(url)
            if response.status_code == 200:
                servers_data = json.loads(response.text)
                servers = []
                for server in servers_data:
                    if server.get("protocol") in ["TCP", "SSL"]:  # Only TCP and SSL are supported for electrum
                        servers.append({"url": server.get("url")})
                
                if servers:
                    self.coin_servers[coin] = servers
                    return servers
                else:
                    print(f"{Fore.YELLOW}No compatible electrum servers found for {coin}{Style.RESET_ALL}")
                    return None
            else:
                print(f"{Fore.RED}Failed to fetch electrum servers for {coin}: HTTP {response.status_code}{Style.RESET_ALL}")
                return None
        except Exception as e:
            print(f"{Fore.RED}Error loading electrum servers for {coin}: {e}{Style.RESET_ALL}")
            return None

    def connect_electrum(self, coin):
        """Connect to an electrum coin network"""
        if coin in self.coin_servers:
            servers = self.coin_servers[coin]
        else:
            # Try to load from GitHub if not in predefined list
            print(f"Fetching {coin} electrum servers from GitHub...")
            github_servers = self.load_electrum_servers(coin)
            if github_servers:
                servers = github_servers
            else:
                print(f"{Fore.YELLOW}No predefined or GitHub electrum servers for {coin}. Please provide them manually.{Style.RESET_ALL}")
                servers = []
                while True:
                    server = input("Enter electrum server URL (or leave empty to finish): ")
                    if not server:
                        break
                    servers.append({"url": server})
                
                if not servers:
                    print(f"{Fore.RED}No servers provided. Connection aborted.{Style.RESET_ALL}")
                    return None
        
        # Format exactly like the working KMDconnect.sh script
        payload = {
            "userpass": self.userpass,
            "method": "electrum",
            "coin": coin,
            "servers": servers
        }
        
        print(f"Connecting to {coin} network...")
        try:
            headers = {'Content-Type': 'application/json'}
            # Use json.dumps to ensure proper JSON formatting
            response = requests.post("http://127.0.0.1:7783", 
                                    data=json.dumps(payload), 
                                    headers=headers)
            
            if response.status_code != 200:
                print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        print(f"{Fore.RED}Error details: {error_json['error']}{Style.RESET_ALL}")
                except:
                    print(f"{Fore.RED}Could not decode error response{Style.RESET_ALL}")
                return None
                
            response_json = response.json()
            if response_json.get("result") == "success":
                self.coins_enabled.add(coin)
                self.current_coin = coin
                print(f"{Fore.GREEN}Connected to {coin} successfully{Style.RESET_ALL}")
                print(f"Address: {response_json.get('address')}")
                print(f"Balance: {response_json.get('balance')}")
                return response_json
            else:
                print(f"{Fore.RED}Failed to connect to {coin}: {response_json}{Style.RESET_ALL}")
                return None
                
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}Error: Could not connect to KDF API. Is KDF running?{Style.RESET_ALL}")
            return None
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Invalid JSON response from API{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}Error sending request: {e}{Style.RESET_ALL}")
            return None

    def connect_ethereum_based(self, coin, config):
        """Connect to Ethereum, BNB or other EVM-based networks"""
        print(f"Connecting to {coin} network...")
        response = self.send_request(config)
        
        if response:
            if response.get("result") == "success":
                self.coins_enabled.add(coin)
                self.current_coin = coin
                print(f"{Fore.GREEN}Connected to {coin} successfully{Style.RESET_ALL}")
                print(f"Address: {response.get('address')}")
                return response
            else:
                print(f"{Fore.RED}Failed to connect to {coin}: {response}{Style.RESET_ALL}")
                return None
        return None

    def get_balance(self, coin=None):
        """Get balance for a coin"""
        if not coin:
            coin = self.current_coin
            
        if not coin:
            print(f"{Fore.RED}No coin selected. Please connect to a coin first.{Style.RESET_ALL}")
            return None
            
        payload = {
            "userpass": self.userpass,
            "method": "my_balance",
            "coin": coin
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post("http://127.0.0.1:7783", 
                               data=json.dumps(payload), 
                               headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            if 'balance' in response_json:
                # Add the coin to enabled coins since we know it's active
                self.coins_enabled.add(coin)
                self.current_coin = coin
                
                print(f"{Fore.GREEN}{coin} Balance:{Style.RESET_ALL}")
                print(f"Address: {response_json.get('address')}")
                print(f"Balance: {response_json.get('balance')}")
                return response_json
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            try:
                error_json = response.json()
                if 'error' in error_json:
                    print(f"{Fore.RED}Error details: {error_json['error']}{Style.RESET_ALL}")
            except:
                pass
        return None

    def get_all_balances(self):
        """Get balances for all enabled coins"""
        if not self.coins_enabled:
            print(f"{Fore.YELLOW}No coins enabled yet. Please connect to coins first.{Style.RESET_ALL}")
            return
            
        balances = []
        for coin in self.coins_enabled:
            payload = {
                "method": "my_balance",
                "coin": coin
            }
            response = self.send_request(payload)
            if response:
                balances.append({
                    "coin": coin,
                    "address": response.get('address'),
                    "balance": response.get('balance')
                })
        
        if balances:
            print(f"{Fore.GREEN}Balances:{Style.RESET_ALL}")
            table = tabulate(balances, headers="keys", tablefmt="pretty")
            print(table)
        else:
            print(f"{Fore.YELLOW}No balance information available{Style.RESET_ALL}")

    def update_coin_prices(self, force=False):
        """Update coin prices from CoinGecko API"""
        # Only update if more than 60 seconds have passed since last update
        current_time = time.time()
        if not force and (current_time - self.last_price_update) < 60:
            return self.coin_prices
            
        coin_ids = []
        coin_symbols = []
        
        # Prepare lists for API
        for coin in self.coins_enabled:
            if coin in self.coingecko_ids:
                coin_ids.append(self.coingecko_ids[coin])
            else:
                coin_symbols.append(coin.lower())
        
        # Don't make API call if no coins to fetch
        if not coin_ids and not coin_symbols:
            return {}
            
        try:
            params = {
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            # Add IDs if available
            if coin_ids:
                params['ids'] = ','.join(coin_ids)
                print(f"Using IDs: {params['ids']}")
                
            # Add symbols if needed (and no IDs are specified)
            if coin_symbols and not coin_ids:
                params['symbols'] = ','.join(coin_symbols)
                print(f"Using symbols: {params['symbols']}")
            
            # Default to free API
            url = "https://api.coingecko.com/api/v3/simple/price"
            headers = {'accept': 'application/json'}
            
            print(f"{Fore.YELLOW}Using CoinGecko Free API{Style.RESET_ALL}")
            
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Update prices cache
                self.coin_prices = data
                self.last_price_update = current_time
                return data
            elif response.status_code == 429:
                print(f"{Fore.RED}CoinGecko API rate limit exceeded. Try again later.{Style.RESET_ALL}")
                return self.coin_prices  # Return cached prices
            else:
                print(f"{Fore.YELLOW}Failed to update prices: HTTP {response.status_code}{Style.RESET_ALL}")
                if response.status_code == 400:
                    print(f"Request URL: {response.request.url}")
                    print(f"Response content: {response.text}")
                return self.coin_prices  # Return cached prices
                
        except Exception as e:
            print(f"{Fore.YELLOW}Error updating coin prices: {e}{Style.RESET_ALL}")
            return self.coin_prices  # Return cached prices

    def get_coin_price(self, coin):
        """Get price for a specific coin"""
        coin_lower = coin.lower()
        
        # Update prices if needed
        prices = self.update_coin_prices()
        
        # Check if price is available by ID
        if coin in self.coingecko_ids:
            coingecko_id = self.coingecko_ids[coin]
            if coingecko_id in prices:
                return prices[coingecko_id]
        
        # Check if price is available by symbol
        if coin_lower in prices:
            return prices[coin_lower]
            
        # Try once more with forced update
        if not prices:
            prices = self.update_coin_prices(force=True)
            
            if coin in self.coingecko_ids:
                coingecko_id = self.coingecko_ids[coin]
                if coingecko_id in prices:
                    return prices[coingecko_id]
            
            if coin_lower in prices:
                return prices[coin_lower]
        
        # Price not found
        return None

    def get_portfolio(self):
        """Get portfolio with balance and value"""
        if not self.coins_enabled:
            print(f"{Fore.YELLOW}No coins enabled yet. Please connect to coins first.{Style.RESET_ALL}")
            return
        
        # Update prices first
        self.update_coin_prices()
        
        # Get balances for all enabled coins
        all_coin_balances = []
        total_value_usd = 0
        
        for coin in self.coins_enabled:
            payload = {
                "userpass": self.userpass,
                "method": "my_balance",
                "coin": coin
            }
            
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post("http://127.0.0.1:7783", 
                                        data=json.dumps(payload), 
                                        headers=headers)
                
                if response.status_code == 200:
                    response_json = response.json()
                    address = response_json.get('address', 'N/A')
                    balance = float(response_json.get('balance', 0))
                    
                    # Get price data
                    price_data = self.get_coin_price(coin)
                    price_usd = 0
                    market_cap = 0
                    change_24h = 0
                    volume_24h = 0
                    
                    if price_data:
                        price_usd = price_data.get('usd', 0)
                        market_cap = price_data.get('usd_market_cap', 0)
                        change_24h = price_data.get('usd_24h_change', 0)
                        volume_24h = price_data.get('usd_24h_vol', 0)
                    
                    # Calculate value
                    value_usd = balance * price_usd
                    total_value_usd += value_usd
                    
                    all_coin_balances.append({
                        "Coin": coin,
                        "Address": address,
                        "Balance": balance,
                        "Price (USD)": price_usd,
                        "Value (USD)": value_usd,
                        "24h Change": f"{change_24h:.2f}%" if change_24h else "N/A"
                    })
            except Exception as e:
                print(f"{Fore.RED}Error getting balance for {coin}: {e}{Style.RESET_ALL}")
        
        if all_coin_balances:
            print(f"\n{Fore.CYAN}=== Portfolio Summary ==={Style.RESET_ALL}")
            # Sort by value (descending)
            all_coin_balances = sorted(all_coin_balances, key=lambda x: x['Value (USD)'], reverse=True)
            
            # Add percentage of portfolio
            for balance in all_coin_balances:
                if total_value_usd > 0:
                    balance["Portfolio %"] = f"{(balance['Value (USD)'] / total_value_usd) * 100:.2f}%"
                else:
                    balance["Portfolio %"] = "N/A"
            
            # Display assets in a table
            table_data = [{
                "Coin": b["Coin"],
                "Address": b["Address"],
                "Balance": f"{b['Balance']:.8f}",
                "Price (USD)": f"${b['Price (USD)']:.4f}",
                "Value (USD)": f"${b['Value (USD)']:.2f}",
                "Portfolio %": b["Portfolio %"],
                "24h Change": b["24h Change"]
            } for b in all_coin_balances]
            
            print(tabulate(table_data, headers="keys", tablefmt="pretty"))
            print(f"\n{Fore.GREEN}Total Portfolio Value: ${total_value_usd:.2f} USD{Style.RESET_ALL}")
            
            # Create a simple pie chart visualization if matplotlib is available
            if 'plt' in globals():
                try:
                    # Only include non-zero balances
                    non_zero = [b for b in all_coin_balances if b['Value (USD)'] > 0]
                    if non_zero:
                        labels = [b['Coin'] for b in non_zero]
                        values = [b['Value (USD)'] for b in non_zero]
                        
                        plt.figure(figsize=(10, 7))
                        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
                        plt.axis('equal')
                        plt.title('Portfolio Allocation')
                        
                        # Save the visualization
                        output_dir = os.path.expanduser("~/kdf_visualizations")
                        os.makedirs(output_dir, exist_ok=True)
                        output_file = os.path.join(output_dir, 'portfolio_allocation.png')
                        plt.savefig(output_file)
                        
                        print(f"{Fore.GREEN}Portfolio visualization saved to:{Style.RESET_ALL} {output_file}")
                        plt.show()
                except Exception as e:
                    print(f"{Fore.YELLOW}Could not create portfolio visualization: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No balance information available{Style.RESET_ALL}")

    def get_orderbook(self, base, rel):
        """Get orderbook for a trading pair and visualize it"""
        payload = {
            "method": "orderbook",
            "base": base,
            "rel": rel
        }
        
        print(f"Getting orderbook for {base}/{rel}...")
        response = self.send_request(payload)
        
        if response:
            # Handle both orderbook response formats
            if 'asks' in response and 'bids' in response:
                asks = response.get('asks', [])
                bids = response.get('bids', [])
                timestamp = response.get('timestamp', 0)
            elif 'result' in response:
                result = response.get('result', {})
                asks = result.get('asks', [])
                bids = result.get('bids', [])
                timestamp = result.get('timestamp', 0)
            else:
                print(f"{Fore.RED}Invalid orderbook response format{Style.RESET_ALL}")
                return None
                
            # Calculate mid price
            mid_price = None
            if asks and bids:
                best_ask = min([float(ask.get('price', 0)) for ask in asks if float(ask.get('price', 0)) > 0])
                best_bid = max([float(bid.get('price', 0)) for bid in bids if float(bid.get('price', 0)) > 0])
                mid_price = (best_ask + best_bid) / 2
                
            # Display summary
            print(f"{Fore.GREEN}Orderbook for {base}/{rel}:{Style.RESET_ALL}")
            print(f"Timestamp: {timestamp}")
            print(f"Number of asks: {len(asks)}")
            print(f"Number of bids: {len(bids)}")
            
            if mid_price:
                print(f"{Fore.CYAN}Mid price: {mid_price:.8f} {rel}/{base}{Style.RESET_ALL}")
            
            # Display asks and bids in tabular format
            if asks:
                print(f"\n{Fore.RED}Top 5 Asks (Sell Orders) - {base} → {rel}:{Style.RESET_ALL}")
                ask_data = []
                for i, ask in enumerate(asks[:5]):
                    price = float(ask.get('price', 0))
                    volume = float(ask.get('maxvolume', 0))
                    total = price * volume
                    ask_data.append({
                        f"Price ({rel}/{base})": price,
                        f"Volume ({base})": volume,
                        f"Total ({rel})": total
                    })
                print(tabulate(ask_data, headers="keys", tablefmt="pretty", floatfmt=".8f"))
            
            if bids:
                print(f"\n{Fore.GREEN}Top 5 Bids (Buy Orders) - {rel} → {base}:{Style.RESET_ALL}")
                bid_data = []
                for i, bid in enumerate(bids[:5]):
                    price = float(bid.get('price', 0))
                    volume = float(bid.get('maxvolume', 0))
                    total = price * volume
                    bid_data.append({
                        f"Price ({rel}/{base})": price,
                        f"Volume ({base})": volume,
                        f"Total ({rel})": total
                    })
                print(tabulate(bid_data, headers="keys", tablefmt="pretty", floatfmt=".8f"))
            
            # Visualize the orderbook
            self.visualize_orderbook(base, rel, asks, bids, mid_price)
            
            return response
        return None

    def visualize_orderbook(self, base, rel, asks, bids, mid_price=None):
        """Visualize the orderbook using matplotlib"""
        if not asks and not bids:
            print(f"{Fore.YELLOW}No orders to visualize{Style.RESET_ALL}")
            return
            
        try:
            # Create a text-based visualization if matplotlib is not available
            if 'plt' not in globals():
                print(f"{Fore.YELLOW}Matplotlib not available. Using text-based visualization.{Style.RESET_ALL}")
                self.visualize_orderbook_text(base, rel, asks, bids, mid_price)
                return
                
            ask_prices = [float(ask.get('price', 0)) for ask in asks]
            ask_volumes = [float(ask.get('maxvolume', 0)) for ask in asks]
            
            bid_prices = [float(bid.get('price', 0)) for bid in bids]
            bid_volumes = [float(bid.get('maxvolume', 0)) for bid in bids]
            
            # Create a new figure
            plt.figure(figsize=(12, 6))
            
            # Plot asks (sell orders) in red
            if ask_prices and ask_volumes:
                plt.bar([str(round(price, 8)) for price in ask_prices[:10]], 
                       ask_volumes[:10], 
                       color='red', 
                       alpha=0.6, 
                       label=f'Asks (Sell {base} for {rel})')
            
            # Plot bids (buy orders) in green
            if bid_prices and bid_volumes:
                plt.bar([str(round(price, 8)) for price in bid_prices[:10]], 
                       bid_volumes[:10], 
                       color='green', 
                       alpha=0.6, 
                       label=f'Bids (Buy {base} with {rel})')
            
            # Add mid price line if available
            if mid_price:
                plt.axhline(y=0, color='blue', linestyle='-', linewidth=2, label=f'Mid Price: {mid_price:.8f} {rel}/{base}')
                plt.text(0, 0, f'Mid: {mid_price:.8f}', color='blue', fontweight='bold')
            
            plt.xlabel(f'Price ({rel}/{base})')
            plt.ylabel(f'Volume ({base})')
            plt.title(f'{base}/{rel} Orderbook')
            plt.xticks(rotation=45)
            plt.legend()
            plt.tight_layout()
            
            # Save the visualization
            output_dir = os.path.expanduser("~/kdf_visualizations")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f'{base}_{rel}_orderbook.png')
            plt.savefig(output_file)
            
            print(f"{Fore.GREEN}Orderbook visualization saved to:{Style.RESET_ALL} {output_file}")
            
            # Show the visualization
            plt.show()
        except Exception as e:
            print(f"{Fore.RED}Error visualizing orderbook: {e}{Style.RESET_ALL}")
            print("Falling back to text-based visualization")
            self.visualize_orderbook_text(base, rel, asks, bids, mid_price)
            
    def visualize_orderbook_text(self, base, rel, asks, bids, mid_price=None):
        """Create a text-based visualization of the orderbook"""
        print(f"\n{Fore.CYAN}==== {base}/{rel} Orderbook Text Visualization ===={Style.RESET_ALL}")
        
        # Sort asks by price (ascending)
        sorted_asks = sorted(asks, key=lambda ask: float(ask.get('price', 0)))
        # Sort bids by price (descending)
        sorted_bids = sorted(bids, key=lambda bid: float(bid.get('price', 0)), reverse=True)
        
        # Get the top asks (lowest prices first)
        top_asks = sorted_asks[:10]
        # Get the top bids (highest prices first)
        top_bids = sorted_bids[:10]
        
        # Find the maximum volume for scaling
        max_volume = 0
        for order in top_asks + top_bids:
            volume = float(order.get('maxvolume', 0))
            if volume > max_volume:
                max_volume = volume
        
        # Define the width of the bar chart
        bar_width = 50
        
        # Print the asks (from highest to lowest price)
        print(f"\n{Fore.RED}ASKS (Sell {base} for {rel}) - Lowest to Highest{Style.RESET_ALL}")
        for ask in reversed(top_asks):
            price = float(ask.get('price', 0))
            volume = float(ask.get('maxvolume', 0))
            bar_length = int((volume / max_volume) * bar_width) if max_volume > 0 else 0
            bar = '█' * bar_length
            print(f"{Fore.RED}Price: {price:.8f} | Volume: {volume:.8f} {base} | {bar}{Style.RESET_ALL}")
        
        # Print a divider
        price_range = ""
        lowest_ask = None
        highest_bid = None
        
        if top_asks:
            lowest_ask = float(sorted_asks[0].get('price', 0))
        if top_bids:
            highest_bid = float(sorted_bids[0].get('price', 0))
            
        if lowest_ask and highest_bid:
            spread = lowest_ask - highest_bid
            price_range = f"Spread: {spread:.8f} ({(spread/highest_bid)*100:.2f}% of bid)"
            
        print(f"\n{Fore.YELLOW}{'=' * 60}")
        if mid_price:
            print(f"MID PRICE: {mid_price:.8f} {rel}/{base}")
        print(f"SPREAD | {price_range}")
        print(f"{'=' * 60}{Style.RESET_ALL}\n")
        
        # Print the bids (from highest to lowest price)
        print(f"{Fore.GREEN}BIDS (Buy {base} with {rel}) - Highest to Lowest{Style.RESET_ALL}")
        for bid in top_bids:
            price = float(bid.get('price', 0))
            volume = float(bid.get('maxvolume', 0))
            bar_length = int((volume / max_volume) * bar_width) if max_volume > 0 else 0
            bar = '█' * bar_length
            print(f"{Fore.GREEN}Price: {price:.8f} | Volume: {volume:.8f} {base} | {bar}{Style.RESET_ALL}")

    def place_order(self, base, rel, price, volume):
        """Place a maker order (setprice)"""
        payload = {
            "userpass": self.userpass,
            "method": "setprice",
            "base": base,
            "rel": rel,
            "price": str(price),
            "volume": str(volume)
        }
        
        print(f"Placing order: Sell {volume} {base} for {rel} at price {price}...")
        headers = {'Content-Type': 'application/json'}
        response = requests.post("http://127.0.0.1:7783", 
                               data=json.dumps(payload), 
                               headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get('result') == 'success' or 'result' in response_json:
                result = response_json.get('result', {})
                uuid = result.get('uuid', 'Unknown')
                print(f"{Fore.GREEN}Order placed successfully{Style.RESET_ALL}")
                print(f"UUID: {uuid}")
                print(f"Details: {json.dumps(result, indent=2)}")
                return response_json
            else:
                print(f"{Fore.RED}Failed to place order: {response_json}{Style.RESET_ALL}")
                return None
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            return None

    def my_orders(self):
        """Get all active orders"""
        payload = {
            "userpass": self.userpass,
            "method": "my_orders"
        }
        
        print("Getting active orders...")
        headers = {'Content-Type': 'application/json'}
        response = requests.post("http://127.0.0.1:7783", 
                               data=json.dumps(payload), 
                               headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            if 'result' in response_json:
                result = response_json.get('result', {})
                maker_orders = result.get('maker_orders', {})
                taker_orders = result.get('taker_orders', {})
                
                if not maker_orders and not taker_orders:
                    print(f"{Fore.YELLOW}No active orders found{Style.RESET_ALL}")
                    return response_json
                
                # Display maker orders
                if maker_orders:
                    print(f"\n{Fore.GREEN}Maker Orders:{Style.RESET_ALL}")
                    for uuid, order in maker_orders.items():
                        print(f"\nUUID: {uuid}")
                        print(f"Base: {order.get('base')}")
                        print(f"Rel: {order.get('rel')}")
                        print(f"Price: {order.get('price')}")
                        print(f"Volume: {order.get('max_base_vol')}")
                        if 'created_at' in order:
                            print(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order.get('created_at')/1000))}")
                
                # Display taker orders
                if taker_orders:
                    print(f"\n{Fore.GREEN}Taker Orders:{Style.RESET_ALL}")
                    for uuid, order in taker_orders.items():
                        print(f"\nUUID: {uuid}")
                        print(f"Base: {order.get('base')}")
                        print(f"Rel: {order.get('rel')}")
                        if 'created_at' in order:
                            print(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order.get('created_at')/1000))}")
                
                return response_json
            else:
                print(f"{Fore.RED}Invalid response format: {response_json}{Style.RESET_ALL}")
                return None
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            return None

    def cancel_order(self, uuid):
        """Cancel an order by UUID"""
        payload = {
            "userpass": self.userpass,
            "method": "cancel_order",
            "uuid": uuid
        }
        
        print(f"Cancelling order {uuid}...")
        headers = {'Content-Type': 'application/json'}
        response = requests.post("http://127.0.0.1:7783", 
                               data=json.dumps(payload), 
                               headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            if response_json.get('result') == 'success':
                print(f"{Fore.GREEN}Order {uuid} cancelled successfully{Style.RESET_ALL}")
                return response_json
            else:
                print(f"{Fore.RED}Failed to cancel order: {response_json}{Style.RESET_ALL}")
                return None
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            return None

    def withdraw(self, coin, to_address, amount):
        """Withdraw funds to an address"""
        payload = {
            "userpass": self.userpass,
            "method": "withdraw",
            "coin": coin,
            "to": to_address,
            "amount": str(amount)
        }
        
        print(f"Withdrawing {amount} {coin} to {to_address}...")
        headers = {'Content-Type': 'application/json'}
        response = requests.post("http://127.0.0.1:7783", 
                               data=json.dumps(payload), 
                               headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            if 'tx_hex' in response_json:
                print(f"{Fore.GREEN}Withdrawal initiated successfully{Style.RESET_ALL}")
                print(f"Transaction hex: {response_json.get('tx_hex')}")
                print(f"Transaction hash: {response_json.get('tx_hash')}")
                
                # Prompt to send the transaction
                confirm = input(f"Send the transaction? (y/n): ")
                if confirm.lower() == 'y':
                    return self.send_raw_transaction(coin, response_json.get('tx_hex'))
                else:
                    print(f"{Fore.YELLOW}Transaction cancelled{Style.RESET_ALL}")
                    return response_json
            else:
                print(f"{Fore.RED}Failed to initiate withdrawal: {response_json}{Style.RESET_ALL}")
                return None
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            return None

    def send_raw_transaction(self, coin, tx_hex):
        """Send a raw transaction to the network"""
        payload = {
            "userpass": self.userpass,
            "method": "send_raw_transaction",
            "coin": coin,
            "tx_hex": tx_hex
        }
        
        print(f"Sending {coin} transaction to network...")
        headers = {'Content-Type': 'application/json'}
        response = requests.post("http://127.0.0.1:7783", 
                               data=json.dumps(payload), 
                               headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            if 'tx_hash' in response_json:
                print(f"{Fore.GREEN}Transaction sent successfully{Style.RESET_ALL}")
                print(f"Transaction hash: {response_json.get('tx_hash')}")
                return response_json
            else:
                print(f"{Fore.RED}Failed to send transaction: {response_json}{Style.RESET_ALL}")
                return None
        else:
            print(f"{Fore.RED}Error: API returned status code {response.status_code}{Style.RESET_ALL}")
            return None

    def show_help(self):
        """Show help information"""
        help_text = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║           Komodo DeFi Framework Manager - Help           ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}Basic Commands:{Style.RESET_ALL}
  help                          - Show this help message
  start                         - Start the KDF daemon
  stop                          - Stop the KDF daemon
  exit, quit                    - Exit the program

{Fore.GREEN}Coin Management:{Style.RESET_ALL}
  connect <coin>                - Connect to a coin network (e.g., connect KMD)
  balance [<coin>]              - Get balance for a coin (default: current coin)
  portfolio                     - Show portfolio with balances and USD values
  price <coin>                  - Show current price information for a coin

{Fore.GREEN}Trading Commands:{Style.RESET_ALL}
  orderbook <base> <rel>        - Get and visualize orderbook for a trading pair
  place <base> <rel> <price> <volume> - Place a maker order
  orders                        - List your active orders
  cancel <uuid>                 - Cancel an order by UUID

{Fore.GREEN}Fund Management:{Style.RESET_ALL}
  withdraw <coin> <address> <amount> - Withdraw funds
  privkey <coin>                - Show private key for a coin (BE CAREFUL!)

{Fore.YELLOW}Examples:{Style.RESET_ALL}
  connect KMD                   - Connect to the KMD network
  orderbook KMD LTC             - Get orderbook for KMD/LTC pair
  place KMD LTC 0.013 10        - Sell 10 KMD for LTC at price 0.013
  portfolio                     - Show your portfolio with USD values
"""
        print(help_text)

    def run(self):
        """Run the interactive console"""
        print(f"""{Fore.CYAN}
╔══════════════════════════════════════════════════════════╗
║           Komodo DeFi Framework Manager v1.0            ║
║                                                          ║
║    Type 'help' for a list of commands or 'exit' to quit  ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

        # Detect and handle environment
        if not os.path.exists(os.path.join(self.kdf_dir, "kdf")) and os.path.exists(os.path.join(self.kdf_dir, "mm2")):
            print(f"{Fore.YELLOW}Detected mm2 binary instead of kdf. Adapting...{Style.RESET_ALL}")
            
        # Auto-detect active coins
        if self.is_kdf_running():
            print(f"{Fore.GREEN}KDF is running. Detecting active coins...{Style.RESET_ALL}")
            self.detect_active_coins()
            
            # Show help automatically at startup
            self.show_help()
        else:
            print(f"{Fore.YELLOW}KDF is not running. Use 'start' to launch KDF and activate coins.{Style.RESET_ALL}")

        while True:
            try:
                if self.current_coin:
                    prompt = f"{Fore.CYAN}KDF[{self.current_coin}]>{Style.RESET_ALL} "
                else:
                    prompt = f"{Fore.CYAN}KDF>{Style.RESET_ALL} "
                    
                command = input(prompt).strip()
                
                if not command:
                    continue
                    
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Process commands
                if cmd in ['exit', 'quit']:
                    print("Exiting...")
                    break
                elif cmd == 'help':
                    self.show_help()
                elif cmd == 'start':
                    if self.start_kdf():
                        # Detect active coins after starting
                        print(f"{Fore.GREEN}Detecting active coins...{Style.RESET_ALL}")
                        self.detect_active_coins()
                elif cmd == 'stop':
                    self.stop_kdf()
                elif cmd == 'connect':
                    if not args:
                        print(f"{Fore.RED}Please specify a coin to connect to{Style.RESET_ALL}")
                    else:
                        coin = args[0].upper()
                        # Handle special cases for EVM networks
                        if coin == 'BNB':
                            # Configuration for BNB Chain from BNBConnect.sh
                            bnb_config = {
                                "method": "enable_eth_with_tokens",
                                "mmrpc": "2.0",
                                "params": {
                                    "ticker": "BNB",
                                    "mm2": 1,
                                    "swap_contract_address": "0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31",
                                    "fallback_swap_contract": "0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31",
                                    "swap_v2_contracts": {
                                        "maker_swap_v2_contract": "0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31",
                                        "taker_swap_v2_contract": "0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31",
                                        "nft_maker_swap_v2_contract": "0xeDc5b89Fe1f0382F9E4316069971D90a0951DB31"
                                    },
                                    "nodes": [
                                        {"url": "https://bsc1.cipig.net:18655", "ws_url": "wss://bsc1.cipig.net:38655"},
                                        {"url": "https://bsc2.cipig.net:18655", "ws_url": "wss://bsc2.cipig.net:38655"},
                                        {"url": "https://bsc3.cipig.net:18655", "ws_url": "wss://bsc3.cipig.net:38655"},
                                        {"url": "https://bsc-rpc.publicnode.com", "ws_url": "wss://bsc-rpc.publicnode.com"},
                                        {"url": "https://block-proxy.komodo.earth/rpc/bnb", "ws_url": "wss://block-proxy.komodo.earth/rpc/bnb/websocket"}
                                    ],
                                    "tx_history": True,
                                    "erc20_tokens_requests": [
                                        {"ticker": "USDT-BEP20", "required_confirmations": 4}
                                    ],
                                    "required_confirmations": 5,
                                    "requires_notarization": False,
                                    "priv_key_policy": "ContextPrivKey"
                                }
                            }
                            self.connect_ethereum_based(coin, bnb_config)
                        else:
                            self.connect_electrum(coin)
                elif cmd == 'balance':
                    if args:
                        self.get_balance(args[0].upper())
                    else:
                        self.get_balance()
                elif cmd == 'balances':
                    self.get_all_balances()
                elif cmd == 'portfolio':
                    self.get_portfolio()
                elif cmd == 'price':
                    if not args:
                        print(f"{Fore.RED}Please specify a coin (e.g., price KMD){Style.RESET_ALL}")
                    else:
                        coin = args[0].upper()
                        price_data = self.get_coin_price(coin)
                        if price_data:
                            print(f"\n{Fore.GREEN}Price Information for {coin}:{Style.RESET_ALL}")
                            print(f"Price (USD): ${price_data.get('usd', 'N/A')}")
                            if 'usd_market_cap' in price_data:
                                print(f"Market Cap: ${price_data.get('usd_market_cap', 'N/A'):,.2f}")
                            if 'usd_24h_vol' in price_data:
                                print(f"24h Volume: ${price_data.get('usd_24h_vol', 'N/A'):,.2f}")
                            if 'usd_24h_change' in price_data:
                                change = price_data.get('usd_24h_change', 0)
                                color = Fore.GREEN if change >= 0 else Fore.RED
                                print(f"24h Change: {color}{change:+.2f}%{Style.RESET_ALL}")
                            if 'last_updated_at' in price_data:
                                timestamp = price_data.get('last_updated_at')
                                update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                                print(f"Last Updated: {update_time}")
                        else:
                            print(f"{Fore.RED}Could not find price information for {coin}{Style.RESET_ALL}")
                elif cmd == 'orderbook':
                    if len(args) < 2:
                        print(f"{Fore.RED}Please specify base and rel coins (e.g., orderbook KMD LTC){Style.RESET_ALL}")
                    else:
                        self.get_orderbook(args[0].upper(), args[1].upper())
                elif cmd == 'place':
                    if len(args) < 4:
                        print(f"{Fore.RED}Please specify base, rel, price, and volume (e.g., place KMD LTC 0.013 10){Style.RESET_ALL}")
                    else:
                        try:
                            base = args[0].upper()
                            rel = args[1].upper()
                            price = float(args[2])
                            volume = float(args[3])
                            self.place_order(base, rel, price, volume)
                        except ValueError:
                            print(f"{Fore.RED}Invalid price or volume. Please enter valid numbers.{Style.RESET_ALL}")
                elif cmd == 'orders':
                    self.my_orders()
                elif cmd == 'cancel':
                    if not args:
                        print(f"{Fore.RED}Please specify the UUID of the order to cancel{Style.RESET_ALL}")
                    else:
                        self.cancel_order(args[0])
                elif cmd == 'withdraw':
                    if len(args) < 3:
                        print(f"{Fore.RED}Please specify coin, address, and amount (e.g., withdraw KMD RAbcdef... 1.0){Style.RESET_ALL}")
                    else:
                        try:
                            coin = args[0].upper()
                            address = args[1]
                            amount = float(args[2])
                            self.withdraw(coin, address, amount)
                        except ValueError:
                            print(f"{Fore.RED}Invalid amount. Please enter a valid number.{Style.RESET_ALL}")
                elif cmd == 'privkey':
                    if not args:
                        print(f"{Fore.RED}Please specify a coin (e.g., privkey KMD){Style.RESET_ALL}")
                    else:
                        # Security warning
                        print(f"{Fore.RED}WARNING: This will display your private key. Make sure no one is watching your screen.{Style.RESET_ALL}")
                        confirm = input("Are you sure you want to continue? (y/n): ")
                        if confirm.lower() == 'y':
                            payload = {
                                "userpass": self.userpass,
                                "method": "show_priv_key",
                                "coin": args[0].upper()
                            }
                            headers = {'Content-Type': 'application/json'}
                            response = requests.post("http://127.0.0.1:7783", 
                                                   data=json.dumps(payload), 
                                                   headers=headers)
                            if response.status_code == 200:
                                response_json = response.json()
                                if 'privkey' in response_json:
                                    print(f"{Fore.YELLOW}Private key for {args[0].upper()}: {response_json.get('privkey')}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.RED}Failed to get private key{Style.RESET_ALL}")
                        else:
                            print("Operation cancelled")
                else:
                    print(f"{Fore.RED}Unknown command: {cmd}. Type 'help' for a list of commands.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' or 'quit' to exit the program.")
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        # Set the script filename
        if len(sys.argv) > 0 and os.path.basename(sys.argv[0]) == "dex.py":
            print(f"Running as dex.py")
        else:
            # Rename this script to dex.py if it's not already
            script_path = os.path.abspath(__file__)
            dir_path = os.path.dirname(script_path)
            new_path = os.path.join(dir_path, "dex.py")
            
            if script_path != new_path and not os.path.exists(new_path):
                try:
                    import shutil
                    shutil.copy(script_path, new_path)
                    os.chmod(new_path, 0o755)  # Make it executable
                    print(f"Created executable copy at {new_path}")
                except Exception as e:
                    print(f"Could not create dex.py: {e}")
        
        manager = KDFManager()
        manager.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        if "ModuleNotFoundError" in str(e):
            print("\nPlease install required dependencies with:")
            print("pip install requests matplotlib numpy tabulate colorama")
