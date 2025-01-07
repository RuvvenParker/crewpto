from xrpl.account import get_balance
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.wallet import generate_faucet_wallet

# Step 1: Create client to connect to the XRPL Testnet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# Step 2: Create wallets for the test network
wallet1 = generate_faucet_wallet(client, debug=True)
wallet2 = generate_faucet_wallet(client, debug=True)
wallet3 = generate_faucet_wallet(client, debug=True)

wallets = {
    "wallet1": wallet1,
    "wallet2": wallet2,
    "wallet3": wallet3,
}

# Check initial balances
print("Initial Balances:")
for wallet_name, wallet in wallets.items():
    print(f"{wallet_name}: {get_balance(wallet.address, client)} drops")

# Step 3: Define the transactions
transactions = [
    {"payer": "wallet1", "payee": "wallet2", "amount": 1000},  # 0.001 XRP
    {"payer": "wallet2", "payee": "wallet3", "amount": 500},   # 0.0005 XRP
    {"payer": "wallet3", "payee": "wallet1", "amount": 1500},  # 0.0015 XRP
]

# Define the transaction fee (10 drops per transaction on XRPL)
TRANSACTION_FEE = 10

# Step 4: Splitwise Algorithm to Check Fees
def simplify_debts_with_fees(transactions, wallets, transaction_fee):
    # Step 4.1: Calculate net balances
    balances = {}
    for transaction in transactions:
        payer = transaction["payer"]
        payee = transaction["payee"]
        amount = transaction["amount"]

        balances[payer] = balances.get(payer, 0) - amount
        balances[payee] = balances.get(payee, 0) + amount

    # Step 4.2: Separate creditors and debtors
    creditors = []
    debtors = []
    for wallet, balance in balances.items():
        if balance > 0:
            creditors.append((wallet, balance))
        elif balance < 0:
            debtors.append((wallet, -balance))

    # Step 4.3: Simplify debts
    creditors.sort(key=lambda x: -x[1])  # Descending balance
    debtors.sort(key=lambda x: -x[1])    # Descending debt
    simplified_transactions = []

    while creditors and debtors:
        creditor, credit_amount = creditors.pop(0)
        debtor, debt_amount = debtors.pop(0)

        # Settle the minimum of credit or debt, including transaction fees
        settlement_amount = min(credit_amount, debt_amount)

        # Ensure the debtor has enough balance to pay the settlement amount + fee
        debtor_wallet_balance = get_balance(wallets[debtor].address, client)
        if debtor_wallet_balance < (settlement_amount + transaction_fee):
            raise ValueError(f"{debtor} does not have enough balance to pay {settlement_amount} + {transaction_fee} drops.")

        # Add transaction to the list
        simplified_transactions.append({
            "from": debtor,
            "to": creditor,
            "amount": settlement_amount,
        })

        # Update remaining balances
        if credit_amount > debt_amount:
            creditors.insert(0, (creditor, credit_amount - settlement_amount))
        elif debt_amount > credit_amount:
            debtors.insert(0, (debtor, debt_amount - settlement_amount))

    return simplified_transactions


# Get the simplified transactions with fees considered
simplified_transactions = simplify_debts_with_fees(transactions, wallets, TRANSACTION_FEE)

# Step 5: Execute Simplified Transactions on XRPL Testnet
print("\nExecuting Simplified Transactions on XRPL Testnet (with fees):")
for txn in simplified_transactions:
    payer_wallet = wallets[txn["from"]]
    payee_wallet = wallets[txn["to"]]
    amount = txn["amount"]

    # Ensure the payer has enough balance to cover the transaction fee
    payer_balance = get_balance(payer_wallet.address, client)
    total_cost = amount + TRANSACTION_FEE
    if payer_balance < total_cost:
        print(f"Insufficient balance in {txn['from']} to pay {amount} drops + {TRANSACTION_FEE} drop fee.")
        continue

    # Create the payment transaction
    payment_tx = Payment(
        account=payer_wallet.address,
        amount=str(amount),  # Amount in drops
        destination=payee_wallet.address,
    )

    # Submit the transaction and wait for a response
    payment_response = submit_and_wait(payment_tx, client, payer_wallet)
    print(f"Transaction from {txn['from']} to {txn['to']} of {amount} drops submitted. Tx hash: {payment_response.result['hash']}")

# Check final balances
print("\nFinal Balances:")
for wallet_name, wallet in wallets.items():
    print(f"{wallet_name}: {get_balance(wallet.address, client)} drops")
