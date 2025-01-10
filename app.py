from flask import Flask, render_template, request, redirect, url_for
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, Tx
from xrpl.transaction import submit_and_wait
from xrpl.account import get_balance
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Step 1: Create a client to connect to the XRPL Testnet
# client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
provider = Web3.HTTPProvider("https://rpc-evm-sidechain.xrpl.org")
web3 = Web3(provider)
# Add the contract ABI and address
contract_abi = [
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [],
		"name": "AllDebtsSettled",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "address",
				"name": "debtor",
				"type": "address"
			},
			{
				"indexed": True,
				"internalType": "address",
				"name": "creditor",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "DebtAdded",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "address",
				"name": "payer",
				"type": "address"
			},
			{
				"indexed": True,
				"internalType": "address",
				"name": "payee",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "DebtSettled",
		"type": "event"
	},
	{
		"stateMutability": "payable",
		"type": "fallback"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_debtor",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "_creditor",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_amount",
				"type": "uint256"
			}
		],
		"name": "addDebt",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address[]",
				"name": "participants",
				"type": "address[]"
			}
		],
		"name": "areAllDebtsSettled",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "balances",
		"outputs": [
			{
				"internalType": "int256",
				"name": "",
				"type": "int256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_creditor",
				"type": "address"
			}
		],
		"name": "settleDebt",
		"outputs": [],
		"stateMutability": "payable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address[]",
				"name": "participants",
				"type": "address[]"
			}
		],
		"name": "simplifyDebts",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"stateMutability": "payable",
		"type": "receive"
	}
]
contract_address = "0xf0aD6F57c66516D35C212f3510B3166E64D5F2F0"  
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Step 2: Create three wallets 
# Replace these with your MetaMask wallet private keys and addresses
wallets = {
    "wallet1": {
        "address": "0xxxxx",  # MetaMask Wallet 1 address
        "private_key": "xxxxx",  # Wallet 1 private key
    },
    "wallet2": {
        "address": "0xxxxx",  # MetaMask Wallet 2 address
        "private_key": "xxxxx",  # Wallet 2 private key
    },
    "wallet3": {
        "address": "0xxxxx",  # MetaMask Wallet 3 address
        "private_key": "xxxxx",  # Wallet 3 private key
    },
}

# Function to get wallet balances
def get_wallet_balances():
    balances = {}
    for wallet_name, wallet in wallets.items():
        balance = web3.eth.get_balance(wallet["address"])  # Balance in Wei
        balances[wallet_name] = web3.from_wei(balance, "ether")  # Convert to XRP
    return balances
@app.route('/contract_balances', methods=['GET'])
def contract_balances():
    balances = {}
    for wallet_name, wallet in wallets.items():
        for creditor_wallet_name, creditor_wallet in wallets.items():
            if wallet_name != creditor_wallet_name:
                # Fetch balance from the smart contract
                balance = contract.functions.balances(wallet["address"], creditor_wallet["address"]).call()

                # Convert to a signed int256 value
                if balance >= 2**255:  # If the value is in the upper half of uint256 range
                    balance -= 2**256  # Interpret it as a negative int256
                                
                # Convert balance to Ether for readability
                if balance < 0:
                    readable_balance = f"-{web3.from_wei(abs(balance), 'ether')}"
                else:
                    readable_balance = web3.from_wei(balance, "ether")
                
                balances[f"{wallet_name} -> {creditor_wallet_name}"] = readable_balance
    
    # Return JSON for API usage or debugging
    return balances

@app.route('/add_debt', methods=['POST'])
def add_debt():
    # Get form data
    sender = request.form.get('sender')  # Wallet adding the debt
    receiver = request.form.get('receiver')  # Wallet receiving the debt
    amount = float(request.form.get('amount'))  # Debt amount

    # Get sender wallet
    sender_wallet = wallets[sender]

    # Get the current gas price
    current_gas_price = web3.eth.gas_price

    try:
        # Build the transaction to call the addDebt function
        txn = contract.functions.addDebt(
            sender_wallet["address"],  # Debtor address
            wallets[receiver]["address"],  # Creditor address
            web3.to_wei(amount, "ether")  # Amount in Wei
        ).build_transaction({
            "from": sender_wallet["address"],
            "gas": 200000,
            "gasPrice": current_gas_price,
            "nonce": web3.eth.get_transaction_count(sender_wallet["address"]),
            "chainId": 1440002,  
        })

        # Sign the transaction with the sender's private key
        signed_txn = web3.eth.account.sign_transaction(txn, sender_wallet["private_key"])

        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Wait for the transaction receipt
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        transaction_validated = tx_receipt["status"] == 1
    except Exception as e:
        print(f"Error while adding debt: {e}")
        transaction_validated = False
        tx_hash = None

    # Fetch wallet balances
    balances = get_wallet_balances()

    # Fetch contract balances
    contract_balances = {}
    for wallet_name, wallet in wallets.items():
        for creditor_wallet_name, creditor_wallet in wallets.items():
            if wallet_name != creditor_wallet_name:
                try:
                    balance = contract.functions.balances(wallet["address"], creditor_wallet["address"]).call()
                    if balance < 0:
                        contract_balances[f"{wallet_name} -> {creditor_wallet_name}"] = f"-{web3.from_wei(abs(balance), 'ether')}"
                    else:
                        contract_balances[f"{wallet_name} -> {creditor_wallet_name}"] = web3.from_wei(balance, "ether")
                except Exception as e:
                    print(f"Error fetching balance for {wallet_name} -> {creditor_wallet_name}: {e}")
                    contract_balances[f"{wallet_name} -> {creditor_wallet_name}"] = "Error"

    return render_template(
        "index.html",
        wallet1_balance=balances["wallet1"],
        wallet2_balance=balances["wallet2"],
        wallet3_balance=balances["wallet3"],
        contract_balances=contract_balances,
        transaction_hash=tx_hash.hex() if tx_hash else None,
        transaction_validated=transaction_validated
    )


@app.route('/')
def index():
    # Fetch wallet balances
    balances = get_wallet_balances()

    # Fetch contract balances
    contract_balances = {}
    for wallet_name, wallet in wallets.items():
        for creditor_wallet_name, creditor_wallet in wallets.items():
            if wallet_name != creditor_wallet_name:
                balance = contract.functions.balances(wallet["address"], creditor_wallet["address"]).call()

                # Handle negative balances
                if balance < 0:
                    contract_balances[f"{wallet_name} -> {creditor_wallet_name}"] = f"-{web3.from_wei(abs(balance), 'ether')}"
                else:
                    contract_balances[f"{wallet_name} -> {creditor_wallet_name}"] = web3.from_wei(balance, "ether")

    return render_template(
        
        "index.html",
        current_gas_price =web3.eth.gas_price,
        wallet1_balance=balances["wallet1"],
        wallet2_balance=balances["wallet2"],
        wallet3_balance=balances["wallet3"],
        contract_balances=contract_balances
    )

@app.route('/send', methods=['POST'])
def send():
    sender = request.form.get('sender')
    receiver = request.form.get('receiver')

    if sender not in wallets or receiver not in wallets:
        return "Invalid sender or receiver wallet", 400

    sender_wallet = wallets[sender]
    receiver_wallet = wallets[receiver]

    try:
        # Fetch the debt
        debt = contract.functions.balances(sender_wallet["address"], receiver_wallet["address"]).call()
        print(f"Debt fetched from contract: {debt}")

        if debt <= 0:
            return f"{sender} has no outstanding debt to {receiver}.", 400

        # Calculate gas price and transaction costs
        current_gas_price = web3.eth.gas_price
        gas_cost = 200000 * current_gas_price

        # Convert debt to Wei if needed
        if isinstance(debt, int): 
            value_in_wei = debt
        else:
            value_in_wei = int(web3.to_wei(float(debt), "ether"))

        # Check sender's balance
        sender_balance = web3.eth.get_balance(sender_wallet["address"])
        print(f"Sender balance: {sender_balance}, Debt in Wei: {value_in_wei}, Gas cost: {gas_cost}")
        
        if sender_balance < value_in_wei + gas_cost:
            return "Insufficient funds to settle the debt.", 400

        # Build and send the transaction
        txn = contract.functions.settleDebt(receiver_wallet["address"]).build_transaction({
            "from": sender_wallet["address"],
            "value": value_in_wei,
            "gas": 200000,
            "gasPrice": current_gas_price,
            "nonce": web3.eth.get_transaction_count(sender_wallet["address"]),
        })

        signed_txn = web3.eth.account.sign_transaction(txn, sender_wallet["private_key"])
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        transaction_validated = tx_receipt["status"] == 1

        # Update and return wallet balances
        balances = get_wallet_balances()
        return redirect(url_for('index'))
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return f"Invalid input: {str(ve)}", 400
    except Exception as e:
        print(f"Error during settlement: {e}")
        return f"Failed to settle debt: {str(e)}", 500

def fetch_all_balances():
    """
    Fetches the Ether/XRP balances for all wallets and the debt balances from the smart contract.
    
    Returns:
        tuple: A tuple containing two dictionaries:
            - wallet_balances: {wallet_name: balance_in_XRP}
            - contract_balances: {"walletA -> walletB": debt_amount_in_XRP}
    """
    wallet_balances = get_wallet_balances()
    contract_balances = {}
    
    for debtor_name, debtor_wallet in wallets.items():
        for creditor_name, creditor_wallet in wallets.items():
            if debtor_name != creditor_name:
                key = f"{debtor_name} -> {creditor_name}"
                try:
                    # Fetch the debt balance from the smart contract
                    debt_wei = contract.functions.balances(debtor_wallet["address"], creditor_wallet["address"]).call()
                    debt_xrp = Web3.from_wei(debt_wei, "ether") 
                    
                    # Format the debt amount
                    if debt_xrp < 0:
                        contract_balances[key] = f"-{abs(debt_xrp)}"
                    else:
                        contract_balances[key] = f"{debt_xrp}"
                except Exception as e:
                    logger.error(f"Error fetching balance for {key}: {e}")
                    contract_balances[key] = "Error"
                    
    return wallet_balances, contract_balances

def parse_simplified_transactions(tx_receipt):
    """
    Parses the transaction receipt to extract simplified transactions.
    
    Args:
        tx_receipt (AttributeDict): The transaction receipt obtained after sending the transaction.
    
    Returns:
        list: A list of dictionaries representing simplified transactions.
              Each dictionary contains 'from', 'to', and 'amount' keys.
    """
    simplified_transactions = []
    try:
        # Extract DebtsSimplified events
        events = contract.events.DebtsSimplified().processReceipt(tx_receipt)
        
        # Create a mapping of participants to their net balances
        net_balances = {}
        for event in events:
            participant = event['args']['participant']
            net_balance_wei = event['args']['netBalance']
            net_balance_xrp = Web3.from_wei(net_balance_wei, "ether") 
            net_balances[participant] = net_balance_xrp
        
        # Separate participants into debtors and creditors
        debtors = []
        creditors = []
        for participant, balance in net_balances.items():
            if balance < 0:
                debtors.append({"address": participant, "amount": abs(balance)})
            elif balance > 0:
                creditors.append({"address": participant, "amount": balance})
        
        # Sort debtors and creditors for efficient processing
        debtors.sort(key=lambda x: x['amount'], reverse=True)
        creditors.sort(key=lambda x: x['amount'], reverse=True)
        
        # Perform debt settlement algorithm
        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debtor = debtors[i]
            creditor = creditors[j]
            
            settlement_amount = min(debtor['amount'], creditor['amount'])
            
            simplified_transactions.append({
                "from": debtor['address'],
                "to": creditor['address'],
                "amount": settlement_amount
            })
            
            # Update amounts
            debtors[i]['amount'] -= settlement_amount
            creditors[j]['amount'] -= settlement_amount
            
            # Move to next debtor or creditor if their amount is settled
            if debtors[i]['amount'] == 0:
                i += 1
            if creditors[j]['amount'] == 0:
                j += 1
                
    except Exception as e:
        logger.error(f"Error parsing simplified transactions: {e}")
    
    return simplified_transactions

def get_wallet_balances():
    """
    Retrieves the Ether/XRP balances for all wallets.
    
    Returns:
        dict: A dictionary mapping each wallet name to its balance in XRP.
    """
    balances = {}
    for wallet_name, wallet in wallets.items():
        try:
            balance_wei = web3.eth.get_balance(wallet["address"])  # Balance in Wei
            balance_xrp = Web3.from_wei(balance_wei, "ether")       
            balances[wallet_name] = balance_xrp
            logger.debug(f"{wallet_name} balance: {balance_xrp} XRP")
        except Exception as e:
            logger.error(f"Error fetching balance for {wallet_name}: {e}")
            balances[wallet_name] = "Error"
    return balances


@app.route('/simplify', methods=['POST'])
def simplify_debts():
    try:
        # Pick one wallet to pay gas
        admin_wallet = wallets["wallet1"]

        # The participants you want to net among:
        participants = [
            wallets["wallet1"]["address"],
            wallets["wallet2"]["address"],
            wallets["wallet3"]["address"],
        ]

        # Build and send the transaction
        current_gas_price = web3.eth.gas_price
        txn = contract.functions.simplifyDebts(participants).build_transaction({
            "from": admin_wallet["address"],
            "gas": 300000,  # Adjust if needed
            "gasPrice": current_gas_price,
            "nonce": web3.eth.get_transaction_count(admin_wallet["address"]),
            "chainId": 1440002,  
        })
        signed_txn = web3.eth.account.sign_transaction(txn, admin_wallet["private_key"])
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        transaction_validated = (tx_receipt["status"] == 1)

    except Exception as e:
        logger.error(f"Error while simplifying debts: {e}")
        return f"Failed to simplify debts: {str(e)}", 500

    # Now read back the final net balances to build a simplified list
    simplified_transactions = get_simplified_transactions(contract, web3, participants)

    # Also fetch all balances for display (optional):
    wallet_balances, contract_balances = fetch_all_balances()  

    # Render template with updated data
    return redirect(url_for('index'))



def simplify_debts_with_fees(transactions):
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

def get_simplified_transactions(contract, web3, participants):
    """
    Reads the final (net) balances from the contract and returns
    a list of simplified 'owed' relationships.
    """
    simplified_txs = []

    for i in range(len(participants)):
        for j in range(len(participants)):
            if i != j:
                amount_wei = contract.functions.balances(participants[i], participants[j]).call()
                if amount_wei > 0:
                    # 'participants[i]' owes 'participants[j]' this amount
                    amount_xrp = web3.from_wei(amount_wei, 'ether') 
                    simplified_txs.append({
                        "from": participants[i],
                        "to": participants[j],
                        "amount": amount_xrp
                    })
    return simplified_txs
  
  
  
if __name__ == '__main__':
    app.run(debug=True)