# Step 1 is connecting to testnet

from xrpl.account import get_balance
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.wallet import generate_faucet_wallet

# Step 1: Create a client to connect to the test network
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

#Step 2: Create three wallets to send money between each other on the test network (We'll probably store this on a csv or xlsx sheet to maintain coherence
# esp. since we have multiple wallets)
wallet1 = generate_faucet_wallet(client, debug=True)
wallet2 = generate_faucet_wallet(client, debug=True)
wallet3 = generate_faucet_wallet(client, debug=True)

# All balances should be *100 000 000 (also store on excel with a time stamp or transaction title)
print("Balances of wallets before Payment tx")

print("wallet1",get_balance(wallet1.address, client))
print("wallet2",get_balance(wallet2.address, client))
print("wallet3",get_balance(wallet2.address, client))

# Before transfer, get the balance of wallet2 and wallet3 for later comparison
before_paymentw2 = get_balance(wallet2.address, client)  # stored for later use
before_paymentw3 = get_balance(wallet3.address, client)  # stored for later use

# Set amount to transfer from wallet2 and wallet3 to wallet1
amt_trf = 1000

# Create a Payment transaction from wallet2 to wallet1 (the actual transaction bit)
payment_tx_wallet2 = Payment(
    account=wallet2.address,
    amount=str(amt_trf),
    destination=wallet1.address,
)

# Submit the payment from wallet2 to wallet1 and wait for the response
payment_response_wallet2 = submit_and_wait(payment_tx_wallet2, client, wallet2)
print("Transaction from wallet2 to wallet1 was submitted")

# Create a Payment transaction from wallet3 to wallet1 (the actual transaction bit)
payment_tx_wallet3 = Payment(
    account=wallet3.address,
    amount=str(amt_trf),
    destination=wallet1.address,
)

# Submit the payment from wallet3 to wallet1 and wait for the response
payment_response_wallet3 = submit_and_wait(payment_tx_wallet3, client, wallet3)
print("Transaction from wallet3 to wallet1 was submitted")

# Create "Tx" requests to look up the transactions on the ledger (To later verify transaction)
tx_response_wallet2 = client.request(Tx(transaction=payment_response_wallet2.result["hash"]))
tx_response_wallet3 = client.request(Tx(transaction=payment_response_wallet3.result["hash"]))

# Check whether the transactions were validated on the ledger (the actual verification)
print("Wallet2 transaction validated:", tx_response_wallet2.result["validated"])
print("Wallet3 transaction validated:", tx_response_wallet3.result["validated"])

# Check balances after 1000 drops each were sent from wallet2 and wallet3 to wallet1
# (Drops are used for simulation purposes instead of XRP for simplicity, please note there's gas fee on top of the amount transferred)
print("Balances of wallets after Payment tx:")

# Display wallet1 balance after receiving from wallet2 and wallet3
print("wallet1", get_balance(wallet1.address, client))

# Deduction on wallet2 (before_paymentw2 shows balance before)
print(f"Deduction on wallet 2:{before_paymentw2} - {amt_trf} - 10 drop gas fees = {get_balance(wallet2.address, client)}")

# Display wallet2 balance after sending payment
print("wallet2", get_balance(wallet2.address, client))

# Deduction on wallet3 (before_paymentw2 shows balance before)
print(f"Deduction on wallet 3:{before_paymentw3} - {amt_trf} - 10 drop gas fees = {get_balance(wallet3.address, client)}")

# Display wallet3 balance after sending payment
print("wallet3", get_balance(wallet3.address, client))
