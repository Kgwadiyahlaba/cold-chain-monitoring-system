// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ColdChainProof {

    struct Alert {
        string deviceId;
        string alertType;
        string timestamp;
        string dataHash;
    }

    Alert[] private alertLog;

    event AlertStored(
        uint256 indexed index,
        string deviceId,
        string alertType,
        string timestamp,
        string dataHash
    );

    function storeAlert(
        string memory deviceId,
        string memory alertType,
        string memory timestamp,
        string memory dataHash
    ) public {
        alertLog.push(Alert(deviceId, alertType, timestamp, dataHash));
        uint256 index = alertLog.length - 1;
        emit AlertStored(index, deviceId, alertType, timestamp, dataHash);
    }

    function getAlertCount() public view returns (uint256) {
        return alertLog.length;
    }

    function getAlert(uint256 index)
        public
        view
        returns (
            string memory deviceId,
            string memory alertType,
            string memory timestamp,
            string memory dataHash
        )
    {
        require(index < alertLog.length, "Alert index out of range");
        Alert memory a = alertLog[index];
        return (a.deviceId, a.alertType, a.timestamp, a.dataHash);
    }

    function getAlertsByDevice(string memory deviceId)
        public
        view
        returns (Alert[] memory)
    {
        uint256 count;
        bytes32 matchId = keccak256(bytes(deviceId));

        for (uint256 i = 0; i < alertLog.length; i++) {
            if (keccak256(bytes(alertLog[i].deviceId)) == matchId) {
                count++;
            }
        }

        Alert[] memory results = new Alert[](count);
        uint256 pos;

        for (uint256 i = 0; i < alertLog.length; i++) {
            if (keccak256(bytes(alertLog[i].deviceId)) == matchId) {
                results[pos] = alertLog[i];
                pos++;
            }
        }
        return results;
    }
}
ColdChainProof.sol
