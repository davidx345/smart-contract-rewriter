// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TestContract
 * @dev A simple smart contract for testing S3 upload functionality
 */
contract TestContract {
    string public message;
    address public owner;
    
    constructor(string memory _message) {
        message = _message;
        owner = msg.sender;
    }
    
    function updateMessage(string memory _newMessage) public {
        require(msg.sender == owner, "Only owner can update message");
        message = _newMessage;
    }
    
    function getMessage() public view returns (string memory) {
        return message;
    }
}