// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Splitwise {
    address public owner;

    // Mapping to track balances between participants
    mapping(address => mapping(address => int256)) public balances;

    event DebtAdded(address indexed debtor, address indexed creditor, uint256 amount);
    event DebtSettled(address indexed payer, address indexed payee, uint256 amount);
    event AllDebtsSettled();

    constructor() {
        owner = msg.sender; // Owner is the creator of the contract
    }

    // Add a debt between two participants (no longer restricted to only owner)
    function addDebt(address _debtor, address _creditor, uint256 _amount) public {
        require(_debtor != _creditor, "Debtor and creditor cannot be the same");
        require(_amount > 0, "Debt amount must be greater than zero");

        // Update balances
        balances[_debtor][_creditor] += int256(_amount);
        balances[_creditor][_debtor] -= int256(_amount);

        emit DebtAdded(_debtor, _creditor, _amount);
    }

    // Define the struct to store the participant and their net balance
    struct ParticipantBalance {
        address participant;
        int256 netBalance;
    }

    function simplifyDebts(address[] memory participants) public {
        uint256 numParticipants = participants.length;

        // Create an array to track the net balance for each participant
        ParticipantBalance[] memory participantBalances = new ParticipantBalance[](numParticipants);

        // Calculate net balances
        for (uint256 i = 0; i < numParticipants; i++) {
            for (uint256 j = i + 1; j < numParticipants; j++) {
                address participant1 = participants[i];
                address participant2 = participants[j];

                int256 netBalance = balances[participant1][participant2];

                if (netBalance > 0) {
                    // Update net balances for participant1 (owed money)
                    participantBalances[i].netBalance += netBalance;
                    // Update net balances for participant2 (owe money)
                    participantBalances[j].netBalance -= netBalance;
                } else if (netBalance < 0) {
                    // Update net balances for participant1 (owe money)
                    participantBalances[i].netBalance += netBalance;
                    // Update net balances for participant2 (owed money)
                    participantBalances[j].netBalance -= netBalance;
                }
            }
        }

        // Now simplify the debts by consolidating them into a smaller set of transactions
        address from;
        address to;
        int256 amount;

        // Loop through participants and identify the payer and the receiver
        for (uint256 i = 0; i < numParticipants; i++) {
            if (participantBalances[i].netBalance > 0) {
                // This participant is owed money, they are the receiver
                to = participantBalances[i].participant;
                amount = participantBalances[i].netBalance;
            } else if (participantBalances[i].netBalance < 0) {
                // This participant owes money, they are the payer
                from = participantBalances[i].participant;
                amount = -participantBalances[i].netBalance;
            }
        }

        // If there is a payer and receiver, execute the simplified debt transaction
        if (from != address(0) && to != address(0)) {
            // Add your logic here to settle the debt
            balances[from][to] = amount;
            balances[to][from] = -amount;
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