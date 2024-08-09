import os
import pandas as pd
import nada_numpy as na
import nada_numpy.client as na_client
import py_nillion_client as nillion
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv
from nada_ai.client import SklearnClient
from common.utils import compute, store_program, store_secrets
import requests
import json

# Load environment variables
load_dotenv()

# Load your training data
df_train = pd.read_csv('usdt_data_cleaned.csv')

# Define features and target variable for training
X_train = df_train[['balance_in_usdt', 'tokenBalance', 'total_nfts']]
y_train = df_train['target_variable']

# Initialize Nillion client
cluster_id = os.getenv("NILLION_CLUSTER_ID")
grpc_endpoint = os.getenv("GRPC_ENDPOINT")
client = SklearnClient(cluster_id=cluster_id, grpc_endpoint=grpc_endpoint)

# Create and train the linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Function to fetch test data from The Graph protocol
def fetch_test_data():
    # Define the endpoint and query for fetching test data
    endpoint = "https://gateway.thegraph.com/api/your-endpoint/subgraphs/id/your-subgraph-id"
    query = """
    {
      accounts(where: {id: "0xd8da6bf26964af9d7eed9e03e53415d37aa96045") {
        id
        balances(where: {token_: {symbol: "USDT"}}) {
          balance
          token {
            decimals
          }
        }
        tokenHolders {
          tokenBalance
        }
        holdings {
          collection {
            symbol
          }
        }
      }
    }
    """
    response = requests.post(endpoint, json={'query': query})
    if response.status_code == 200:
        data = response.json()
        # Process and return the data
        return process_test_data(data)
    else:
        print(f"Failed to fetch test data: {response.status_code}")
        return None

def process_test_data(data):
    # Process the fetched data into a DataFrame similar to the training data
    accounts = data['data']['accounts']
    rows = []
    for account in accounts:
        balance_in_usdt = sum(
            int(balance['balance']) / (10 ** int(balance['token']['decimals']))
            for balance in account['balances']
        )
        token_balance = sum(
            float(holder['tokenBalance'])
            for holder in account['tokenHolders']
        )
        total_nfts = len(account['holdings'])
        rows.append({
            'account_id': account['id'],
            'balance_in_usdt': balance_in_usdt,
            'tokenBalance': token_balance,
            'total_nfts': total_nfts
        })
    return pd.DataFrame(rows)

# Fetch and process the test data
df_test = fetch_test_data()

# Define features for testing
X_test = df_test[['balance_in_usdt', 'tokenBalance', 'total_nfts']]

# Predict using the trained model
predictions = model.predict(X_test)

# Add predictions to the test DataFrame
df_test['predicted_target'] = predictions

# Save the predictions to a CSV file
df_test.to_csv('usdt_data_predictions.csv', index=False)

print("Model training complete and predictions saved to 'usdt_data_predictions.csv'.")
