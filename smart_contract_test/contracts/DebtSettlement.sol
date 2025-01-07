// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DebtSettlement {
    address public wallet1;
    address public wallet2;
    address public wallet3;
    uint256 public totalDebt;
    uint256 public amountPaid;

    mapping(address => uint256) public payments;

    event PaymentReceived(address payer, uint256 amount);
    event DebtSettled(address settledBy);

    constructor(address _wallet1, address _wallet2, address _wallet3, uint256 _totalDebt) {
        wallet1 = _wallet1;
        wallet2 = _wallet2;
        wallet3 = _wallet3;
        totalDebt = _totalDebt;
        amountPaid = 0;
    }

    modifier onlyWallet1() {
        require(msg.sender == wallet1, "Only wallet1 can call this");
        _;
    }

    function payDebt() public payable {
        require(msg.sender == wallet2 || msg.sender == wallet3, "Only wallet2 or wallet3 can pay");
        require(msg.value > 0, "Payment must be greater than zero");

        payments[msg.sender] += msg.value;
        amountPaid += msg.value;

        emit PaymentReceived(msg.sender, msg.value);

        if (amountPaid >= totalDebt) {
            emit DebtSettled(wallet1);
        }
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }

    function withdraw() public onlyWallet1 {
        require(amountPaid >= totalDebt, "Debt not fully paid");

        uint256 payout = address(this).balance;
        payable(wallet1).transfer(payout);
    }

    function isDebtSettled() public view returns (bool) {
        return amountPaid >= totalDebt;
    }
}