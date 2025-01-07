// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Splitwise {
    address public owner;

    // Mapping to track balances between participants
    mapping(address => mapping(address => int256)) public balances;

    event DebtAdded(address indexed debtor, address indexed creditor, uint256 amount);
    event DebtSettled(address indexed payer, address indexed payee, uint256 amount);
    event AllDebtsSettled();

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the owner can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender; // Owner is the creator of the contract
    }

    // Add a debt between two participants
    function addDebt(address _debtor, address _creditor, uint256 _amount) public onlyOwner {
        require(_debtor != _creditor, "Debtor and creditor cannot be the same");
        require(_amount > 0, "Debt amount must be greater than zero");

        // Update balances
        balances[_debtor][_creditor] += int256(_amount);
        balances[_creditor][_debtor] -= int256(_amount);

        emit DebtAdded(_debtor, _creditor, _amount);
    }

    // Simplify debts between participants
    function simplifyDebts(address[] memory participants) public onlyOwner {
        for (uint256 i = 0; i < participants.length; i++) {
            for (uint256 j = i + 1; j < participants.length; j++) {
                address participant1 = participants[i];
                address participant2 = participants[j];

                int256 netBalance = balances[participant1][participant2];

                if (netBalance > 0) {
                    balances[participant1][participant2] = netBalance;
                    balances[participant2][participant1] = -netBalance;
                } else {
                    balances[participant1][participant2] = 0;
                    balances[participant2][participant1] = 0;
                }
            }
        }
    }

    // Settle a debt between two participants
    function settleDebt(address _creditor) public payable {
        int256 debt = balances[msg.sender][_creditor];
        require(debt > 0, "No debt to settle");
        require(msg.value >= uint256(debt), "Insufficient payment");

        // Update balances
        balances[msg.sender][_creditor] -= debt;
        balances[_creditor][msg.sender] += debt;

        // Transfer funds to the creditor
        payable(_creditor).transfer(msg.value);

        emit DebtSettled(msg.sender, _creditor, msg.value);
    }

    // Check if all debts are settled
    function areAllDebtsSettled(address[] memory participants) public view returns (bool) {
        for (uint256 i = 0; i < participants.length; i++) {
            for (uint256 j = 0; j < participants.length; j++) {
                if (balances[participants[i]][participants[j]] != 0) {
                    return false;
                }
            }
        }
        return true;
    }
}
