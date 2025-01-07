#i j modified stuff from a github repo: 
#https://github.com/XRPLF/xrpl-py?tab=readme-ov-file 
#We can work on these as function calls before working on our UI and all that

#Step 1 is connecting to testnet

from xrpl.account import get_balance
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.wallet import generate_faucet_wallet

# Step 1: Create a client to connect to the test network
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

#Step 2: Create two wallets to send money between on the test network (We'll probably store this generated waller on a csv or xlsx sheet to maintain coherence
# esp. since we have multiple wallets and we dont want to keep generating new wallets each time)
wallet1 = generate_faucet_wallet(client, debug=True)
wallet2 = generate_faucet_wallet(client, debug=True)


# Both balances should be *100 000 000 (also store on excel with a time stamp or transaction title)
print("Balances of wallets before Payment tx")

print("wallet1",get_balance(wallet1.address, client))
print("wallet2",get_balance(wallet2.address, client))

before_paymentw1 = get_balance(wallet1.address, client) #stored for later use
print(len(str(before_paymentw1)))

#set amount to trf from wallet1 to wallet2: 
amt_trf = 1000

# Create a Payment transaction from wallet1 to wallet2 (the actual transaction bit)
payment_tx = Payment(
    account=wallet1.address,
    amount=str(amt_trf),
    destination=wallet2.address,
)

# Submit the payment to the network and wait to see a response

#   It also signs the transaction with wallet1 to prove you own the account you're paying from.
#[Third argument is the signature - we can use this for the verification? or maybe we'll see how after incorporating EVM SC]
payment_response = submit_and_wait(payment_tx, client, wallet1)
print("Transaction was submitted")

# Create a "Tx" request to look up the transaction on the ledger (To later verify transaction - requirement for fulfilling goals)
tx_response = client.request(Tx(transaction=payment_response.result["hash"]))

# Check whether the transaction was actually validated on ledger (the actual verification)
print("Validated:", tx_response.result["validated"])

# Check balances after 1000 drops (.001 XRP) was sent from wallet1 to wallet2
#(Drops are used for simulation purposes instead of XRP for simplicity, pls note there's gas fee on top of the amount transferred)
print("Balances of wallets after Payment tx:")
print("wallet1", get_balance(wallet1.address, client))
print(f"Deduction on wallet 1:{before_paymentw1} - {amt_trf} - 10 drop gas fees = {get_balance(wallet1.address, client)}")
print("wallet2", get_balance(wallet2.address, client), "as wallet2 doesnt incur gas fees so its updated as per normal")
