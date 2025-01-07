const hre = require("hardhat");

async function main() {
    // Compile and get the contract factory
    const Splitwise = await hre.ethers.getContractFactory("Splitwise");

    console.log("Deploying contract...");

    // Deploy the contract
    const splitwise = await Splitwise.deploy();

    // Wait for the contract to be deployed
    await splitwise.deploymentTransaction().wait();

    console.log("Contract deployed to:", splitwise.target);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});


