const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Splitwise Contract", function () {
    let Splitwise, splitwise, owner, addr1, addr2;

    beforeEach(async function () {
        // Deploy the contract
        Splitwise = await ethers.getContractFactory("Splitwise");
        splitwise = await Splitwise.deploy();
        await splitwise.deployed();

        // Get test accounts
        [owner, addr1, addr2] = await ethers.getSigners();
    });

    it("Should add a debt correctly", async function () {
        await splitwise.addDebt(addr1.address, addr2.address, 100);
        const balance = await splitwise.balances(addr1.address, addr2.address);
        expect(balance).to.equal(100);
    });

    it("Should settle debt correctly", async function () {
        await splitwise.addDebt(addr1.address, addr2.address, 100);

        // addr1 pays addr2
        await splitwise.connect(addr1).settleDebt(addr2.address, { value: ethers.utils.parseEther("0.1") });

        const balance = await splitwise.balances(addr1.address, addr2.address);
        expect(balance).to.equal(0);
    });

    it("Should check if all debts are settled", async function () {
        await splitwise.addDebt(addr1.address, addr2.address, 100);

        // addr1 pays addr2
        await splitwise.connect(addr1).settleDebt(addr2.address, { value: ethers.utils.parseEther("0.1") });

        const participants = [addr1.address, addr2.address];
        const allSettled = await splitwise.areAllDebtsSettled(participants);
        expect(allSettled).to.equal(true);
    });
});
