from flask import Flask, render_template, request
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.account import get_balance
from xrpl.wallet import generate_faucet_wallet

app = Flask(__name__)

# Step 1: Create a client to connect to the XRPL Testnet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# Step 2: Create three wallets for the demo
wallet1 = generate_faucet_wallet(client, debug=True)
wallet2 = generate_faucet_wallet(client, debug=True)
wallet3 = generate_faucet_wallet(client, debug=True)

@app.route('/')
def index():
    # Display wallet balances on the home page
    balance1 = get_balance(wallet1.classic_address, client)
    balance2 = get_balance(wallet2.classic_address, client)
    balance3 = get_balance(wallet3.classic_address, client)
    return render_template(
        "index.html",
        wallet1_balance=balance1,
        wallet2_balance=balance2,
        wallet3_balance=balance3
    )

@app.route('/send', methods=['POST'])
def send():
    # Get amount and sender/receiver info from the form
    sender = request.form.get('sender')
    receiver = request.form.get('receiver')
    amount = int(request.form.get('amount')) * 1000  # Convert XRP to drops

    # Map sender and receiver to the wallet objects
    wallets = {
        "wallet1": wallet1,
        "wallet2": wallet2,
        "wallet3": wallet3,
    }
    sender_wallet = wallets[sender]
    receiver_wallet = wallets[receiver]

    # Create a Payment transaction
    payment_tx = Payment(
        account=sender_wallet.classic_address,
        amount=str(amount),
        destination=receiver_wallet.classic_address,
    )

    # Submit the transaction and wait for a response
    payment_response = submit_and_wait(payment_tx, client, sender_wallet)

    # Validate the transaction
    tx_response = client.request(Tx(transaction=payment_response.result["hash"]))
    transaction_validated = tx_response.result["validated"]

    # Get updated balances
    balance1 = get_balance(wallet1.classic_address, client)
    balance2 = get_balance(wallet2.classic_address, client)
    balance3 = get_balance(wallet3.classic_address, client)

    return render_template(
        "index.html",
        wallet1_balance=balance1,
        wallet2_balance=balance2,
        wallet3_balance=balance3,
        transaction_hash=payment_response.result["hash"],
        transaction_validated=transaction_validated
    )

if __name__ == '__main__':
    app.run(debug=True)
