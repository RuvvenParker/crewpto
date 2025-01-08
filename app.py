from flask import Flask, render_template, request
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.account import get_balance
from web3 import Web3

app = Flask(__name__)

# Step 1: Create a client to connect to the XRPL Testnet
# client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
provider = Web3.HTTPProvider("https://rpc-evm-sidechain.xrpl.org")
web3 = Web3(provider)

# Step 2: Create three wallets for the demo
# Replace these with your MetaMask wallet private keys and addresses
wallets = {
    "wallet1": {
        "address": "0x567788dc1303FFe0b5D07E98f4055332c80076bD",  # MetaMask Wallet 1 address
        "private_key": "4a959af2b312c1500a19e2422cb60c1396a0a945b640fb2d09bfef6dcea33605",  # Wallet 1 private key
    },
    "wallet2": {
        "address": "0x78F7627c644b6cE7Edd533eF13C90Aa7314296FE",  # MetaMask Wallet 2 address
        "private_key": "7423d857ae7f04392eced58eba93f0b1fa4c59fe8270adbcc6386289cd9fd07d",  # Wallet 2 private key
    },
    "wallet3": {
        "address": "0xAf8B5E16015e4261F30F3750d41cE5eDf838c8bc",  # MetaMask Wallet 3 address
        "private_key": "9881f20d2d871db1d6292b572dd9b4d01174d9f0c3871ad458fea8ba7c8285c0",  # Wallet 3 private key
    },
}

# Function to get wallet balances
def get_wallet_balances():
    balances = {}
    for wallet_name, wallet in wallets.items():
        balance = web3.eth.get_balance(wallet["address"])  # Balance in Wei
        balances[wallet_name] = web3.from_wei(balance, "ether")  # Convert to XRP
    return balances


@app.route('/')
def index():
    # Fetch wallet balances
    balances = get_wallet_balances()
    return render_template(
        "index.html",
        wallet1_balance=balances["wallet1"],
        wallet2_balance=balances["wallet2"],
        wallet3_balance=balances["wallet3"]
    )


@app.route('/send', methods=['POST'])
def send():
    # Get sender, receiver, and amount from form
    sender = request.form.get('sender')
    receiver = request.form.get('receiver')
    amount = float(request.form.get('amount'))  # Amount in XRP

    # Get sender and receiver wallets
    sender_wallet = wallets[sender]
    receiver_wallet = wallets[receiver]

    # Get the current gas price from the network
    current_gas_price = web3.eth.gas_price

    # Prepare the transaction
    txn = {
        "from": sender_wallet["address"],
        "to": receiver_wallet["address"],
        "value": web3.to_wei(amount, "ether"),  # Convert XRP to Wei
        "gas": 21000,  # Standard gas limit for transfers
        "gasPrice": current_gas_price + web3.to_wei("2", "gwei"),  # Add a tip to current gas price
        "nonce": web3.eth.get_transaction_count(sender_wallet["address"]),
        "chainId": 1440002,  # Replace with the correct chain ID for XRPL EVM Sidechain
    }

    # Sign the transaction
    signed_txn = web3.eth.account.sign_transaction(txn, sender_wallet["private_key"])

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    # Wait for the transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    transaction_validated = tx_receipt["status"] == 1

    # Fetch updated wallet balances
    balances = get_wallet_balances()

    return render_template(
        "index.html",
        wallet1_balance=balances["wallet1"],
        wallet2_balance=balances["wallet2"],
        wallet3_balance=balances["wallet3"],
        transaction_hash=tx_hash.hex(),
        transaction_validated=transaction_validated
    )



@app.route('/simplify', methods=['POST'])
def simplify():
    # Example input transactions (replace with actual logic)
    transactions = [
        {"payer": "wallet1", "payee": "wallet2", "amount": 1000},
        {"payer": "wallet2", "payee": "wallet3", "amount": 500},
        {"payer": "wallet3", "payee": "wallet1", "amount": 1500},
    ]

    # Simplify transactions using your Splitwise algorithm
    simplified_transactions = simplify_debts_with_fees(transactions)

    # Execute simplified transactions
    for txn in simplified_transactions:
        sender_wallet = wallets[txn["from"]]
        receiver_wallet = wallets[txn["to"]]
        amount = txn["amount"]

        # Prepare the transaction
        txn = {
            "from": sender_wallet["address"],
            "to": receiver_wallet["address"],
            "value": web3.to_wei(amount, "ether"),  # Convert to Wei
            "gas": 21000,
            "gasPrice": web3.to_wei("5", "gwei"),
            "nonce": web3.eth.get_transaction_count(sender_wallet["address"]),
        }

        # Sign and send the transaction
        signed_txn = web3.eth.account.sign_transaction(txn, sender_wallet["private_key"])
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    # Fetch updated balances
    balances = get_wallet_balances()

    return render_template(
        "index.html",
        wallet1_balance=balances["wallet1"],
        wallet2_balance=balances["wallet2"],
        wallet3_balance=balances["wallet3"]
    )


def simplify_debts_with_fees(transactions):
    # Example Splitwise algorithm for simplification
    balances = {}
    for txn in transactions:
        payer = txn["payer"]
        payee = txn["payee"]
        amount = txn["amount"]
        balances[payer] = balances.get(payer, 0) - amount
        balances[payee] = balances.get(payee, 0) + amount

    # Generate simplified transactions
    simplified_transactions = []
    for payer, balance in balances.items():
        if balance < 0:
            for payee, payee_balance in balances.items():
                if payee_balance > 0:
                    settlement = min(-balance, payee_balance)
                    simplified_transactions.append({
                        "from": payer,
                        "to": payee,
                        "amount": settlement,
                    })
                    balances[payer] += settlement
                    balances[payee] -= settlement

    return simplified_transactions


if __name__ == '__main__':
    app.run(debug=True)