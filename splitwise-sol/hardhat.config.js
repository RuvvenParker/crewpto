require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.28",
  networks: {
    hardhat: {}, // Local Hardhat network
    xrplEvmTestnet: {
      url: "https://rpc-evm-sidechain.xrpl.org", // XRPL EVM Sidechain Testnet RPC URL
      chainId: 1440002, // Chain ID for XRPL EVM Sidechain Testnet
      accounts: ["4a959af2b312c1500a19e2422cb60c1396a0a945b640fb2d09bfef6dcea33605"], // Replace with your MetaMask private key
    },
  },
};
