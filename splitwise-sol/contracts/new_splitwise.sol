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

        // Create an array to track net balances
        int256[] memory netBalances = new int256[](numParticipants);

        // Calculate net balances for each participant
        for (uint256 i = 0; i < numParticipants; i++) {
            for (uint256 j = 0; j < numParticipants; j++) {
                if (i != j) {
                    netBalances[i] += balances[participants[j]][participants[i]];
                }
            }
        }

        // Reset all balances to 0
        for (uint256 i = 0; i < numParticipants; i++) {
            for (uint256 j = 0; j < numParticipants; j++) {
                balances[participants[i]][participants[j]] = 0;
            }
        }

        // Reconstruct simplified debts
        for (uint256 i = 0; i < numParticipants; i++) {
            if (netBalances[i] > 0) {
                for (uint256 j = 0; j < numParticipants; j++) {
                    if (netBalances[j] < 0) {
                        int256 settlement = netBalances[i] < -netBalances[j] ? netBalances[i] : -netBalances[j];
                        balances[participants[j]][participants[i]] += settlement;
                        netBalances[i] -= settlement;
                        netBalances[j] += settlement;

                        if (netBalances[i] == 0) {
                            break;
                        }
                    }
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

    // Fallback function to receive Ether
    receive() external payable {}

    // Fallback function with data (optional, not necessary if only receiving plain Ether)
    fallback() external payable {}
}