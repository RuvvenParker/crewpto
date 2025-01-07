from flask import Flask, render_template, request
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.account import get_balance
from xrpl.wallet import Wallet, generate_faucet_wallet

app = Flask(__name__)

# Connect to the XRPL Testnet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# Pre-defined wallets
wallet1 = Wallet.from_seed("sEdS7zNuahixdQQLx5AFpvQxojVb2ko")  # Replace with your Wallet 1 secret
wallet2 = generate_faucet_wallet(client, debug=True)

@app.route('/')
def index():
    # Get balances of both wallets
    balance1 = get_balance(wallet1.classic_address, client)
    balance2 = get_balance(wallet2.classic_address, client)
    return render_template("index.html", wallet1_balance=balance1, wallet2_balance=balance2)

@app.route('/send', methods=['POST'])
def send():
    # Get the amount to transfer from the form
    amount = request.form.get('amount')
    
    # Create a payment transaction
    payment_tx = Payment(
        account=wallet1.classic_address,
        amount=str(int(amount) * 1000),  # Convert XRP to drops
        destination=wallet2.classic_address
    )

    # Submit the transaction
    payment_response = submit_and_wait(payment_tx, client, wallet1)

    # Get updated balances
    balance1 = get_balance(wallet1.classic_address, client)
    balance2 = get_balance(wallet2.classic_address, client)

    # Render the updated page
    return render_template(
        "index.html",
        wallet1_balance=balance1,
        wallet2_balance=balance2,
        transaction_hash=payment_response.result["hash"],
        transaction_validated=payment_response.result["validated"]
    )

if __name__ == '__main__':
    app.run(debug=True)

