import requests
import json
import pandas as pd

# Define the API endpoints and queries
endpoints = {
    "usdt": "https://gateway.thegraph.com/api/d1e6fecbcbbaab623a5d5e1ae7343fb7/subgraphs/id/35AYsvtJ7SjD93JZcjHK7KTSFyC8h74YHkg2hTxRsRer",
    "ens": "https://gateway.thegraph.com/api/d1e6fecbcbbaab623a5d5e1ae7343fb7/subgraphs/id/GyijYxW9yiSRcEd5u2gfquSvneQKi5QuvU3WZgFyfFSn",
    "nft": "https://gateway.thegraph.com/api/d1e6fecbcbbaab623a5d5e1ae7343fb7/subgraphs/id/CBf1FtUKFnipwKVm36mHyeMtkuhjmh4KHzY3uWNNq5ow"
}

queries = {
    "usdt": """
    {
      accounts(first:1000) {
        balances(where: {token_: {symbol: "USDT", decimals: "6"}, balance_gte: "1000"}) {
          balance
          token {
            symbol
            decimals
          }
        }
        id
      }
    }
    """,
    "ens": """
    {
      tokenHolders(first: 67, where: {tokenBalance_gt: "1"}) {
        tokenBalance
      }
    }
    """,
    "nft": """
    query MyQuery {
      accounts(first: 67) {
        id
        holdings {
          collection {
            symbol
          }
        }
      }
    }
    """
}

def fetch_data(endpoint, query):
    response = requests.post(endpoint, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Query failed with status code {response.status_code}")
        return None

# Fetch USDT data
usdt_data = fetch_data(endpoints["usdt"], queries["usdt"])
if usdt_data:
    accounts = usdt_data.get("data", {}).get("accounts", [])
    rows = []
    for account in accounts:
        account_id = account.get("id")
        for balance_info in account.get("balances", []):
            balance_in_usdt = int(balance_info["balance"]) / (10 ** int(balance_info["token"]["decimals"]))
            rows.append({
                "account_id": account_id,
                "balance_in_usdt": balance_in_usdt
            })
    usdt_df = pd.DataFrame(rows)

# Fetch ENS token balance data and add to DataFrame
ens_data = fetch_data(endpoints["ens"], queries["ens"])
if ens_data and "data" in ens_data and "tokenHolders" in ens_data["data"]:
    token_balances = [float(holder["tokenBalance"]) for holder in ens_data["data"]["tokenHolders"]]
    if len(token_balances) >= len(usdt_df):
        usdt_df['tokenBalance'] = token_balances[:len(usdt_df)]
    else:
        usdt_df['tokenBalance'] = token_balances + [0] * (len(usdt_df) - len(token_balances))

# Fetch NFT data and add to DataFrame
nft_data = fetch_data(endpoints["nft"], queries["nft"])
if nft_data:
    nft_counts = []
    for account in nft_data['data']['accounts']:
        total_nfts = len(account['holdings'])
        nft_counts.append({'account_id': account['id'], 'total_nfts': total_nfts})
    nft_df = pd.DataFrame(nft_counts)
    usdt_df = pd.merge(usdt_df, nft_df, how='left', left_on='account_id', right_on='account_id')
    usdt_df['total_nfts'] = usdt_df['total_nfts'].fillna(0)

# Clean the DataFrame
usdt_df = usdt_df.drop(columns=['symbol', 'decimals', 'balance_in_wei'], errors='ignore')

# Remove the first two rows if needed
usdt_df = usdt_df.iloc[2:].reset_index(drop=True)

# Save the updated DataFrame to a new CSV file
usdt_df.to_csv('usdt_data_cleaned.csv', index=False)

print("Data has been saved to 'usdt_data_cleaned.csv'")

import pandas as pd
import numpy as np

# Load the CSV file
file_path = 'usdt_data_cleaned.csv'
df = pd.read_csv(file_path)

# Normalize balance_in_usdt and total_nfts to create a target variable between 0 and 1

df['normalized_balance'] = (df['balance_in_usdt'] - df['balance_in_usdt'].min()) / (df['balance_in_usdt'].max() - df['balance_in_usdt'].min())
df['normalized_nfts'] = (df['total_nfts'] - df['total_nfts'].min()) / (df['total_nfts'].max() - df['total_nfts'].min())

df['target_variable'] = 0.7 * df['normalized_balance'] + 0.3 * df['normalized_nfts']

df = df.drop(columns=['normalized_balance', 'normalized_nfts'])

# Save the updated dataframe back to the same CSV file
df.to_csv(file_path, index=False)

print("Target variable between 0 and 1 added, and CSV updated successfully.")
