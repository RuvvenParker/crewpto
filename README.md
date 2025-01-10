# Crewpto

**FinTech Summit Hackathon**

Crewpto is a blockchain-based platform designed to simplify group expense management by integrating Metamask, a smart contract, and the XRPL EVM Sidechain Testnet. The solution addresses the inefficiencies of existing platforms by combining expense tracking with seamless settlement, all within a decentralized ecosystem. We ensure that group expenses are recorded transparently on the blockchain, with all transactions verifiable via a blockchain explorer. By combining user-friendliness with the security and efficiency of blockchain technology, we’ve redefined shared expense management, offering a modern, cross-border solution for groups worldwide.

**Note:** Everything is running on the testnet, ensuring that all transactions are secure for testing purposes. No real funds are involved during testing.

## Installation and Usage
To run this project, follow these steps:

1. Clone the repository:
   `git clone <<repo-url>>`

2. Navigate into the project directory:
   `cd crewpto`

3. Install the required dependencies on terminal:
   ```pip install flask
   pip install xrpl-py
   `pip install web3```

**Note:** For security reasons, we've removed the private and public keys for the three wallets in the code. You must input the private and public keys for the three wallets in the app.py file before running the application.

4. After setting up the private and public keys in app.py, run the app:
   `python app.py`
The app will start a local server. Open a browser and navigate to http://127.0.0.1:5000/ to access the platform.

## Smart Contract

The smart contract for the platform can be found in the splitwise-sol folder under contracts named new_splitwise.sol. This smart contract handles the logic for splitting and tracking expenses on the blockchain.

## Folders Structures

- static: Contains the css folder with styles for the platform.
- templates: Contains the index.html file, which is the main webpage of the platform.
- splitwise-sol: Contains our smart contract files, specifically new_splitwise.sol.
- app.py: The main Python application file, which runs the Flask server.
- Other Files: These files are previous work in progress and may not be fully functional at this time.

## Acknowledgements

Thanks to the NUS FinTech Summit Hackathon organizers for this opportunity to showcase Crewpto.
Special thanks to the XRPL community for their support in building decentralized solutions.

   
