// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

contract ContentVerification is Ownable {
    struct Record {
        bytes32 fingerprint;       // SHA-256 of canonical evidence JSON
        bytes32 contentId;         // keccak256 of source URL
        string sourceUrl;
        uint256 timestamp;
        address submitter;
        bool isRegistered;
    }

    mapping(uint256 => Record) public records;
    mapping(bytes32 => uint256) public fingerprintToRecordId;
    mapping(bytes32 => bool) public fingerprintExists;

    uint256 public recordCount;

    event RecordRegistered(
        uint256 indexed recordId,
        bytes32 indexed fingerprint,
        bytes32 indexed contentId,
        string sourceUrl,
        address submitter,
        uint256 timestamp
    );

    event VerificationChecked(
        uint256 indexed recordId,
        bytes32 fingerprint,
        bool isValid
    );

    constructor() Ownable(msg.sender) {
        recordCount = 0;
    }

    /**
     * @notice Register a fingerprinted evidence record on-chain.
     * @param _fingerprint SHA-256 hash of the canonical evidence JSON
     * @param _contentId keccak256 hash of the source URL
     * @param _sourceUrl The discovered social media post URL
     */
    function registerRecord(
        bytes32 _fingerprint,
        bytes32 _contentId,
        string memory _sourceUrl
    ) external onlyOwner {
        require(!fingerprintExists[_fingerprint], "Fingerprint already registered");

        uint256 recordId = recordCount;
        recordCount++;

        records[recordId] = Record({
            fingerprint: _fingerprint,
            contentId: _contentId,
            sourceUrl: _sourceUrl,
            timestamp: block.timestamp,
            submitter: msg.sender,
            isRegistered: true
        });

        fingerprintToRecordId[_fingerprint] = recordId;
        fingerprintExists[_fingerprint] = true;

        emit RecordRegistered(recordId, _fingerprint, _contentId, _sourceUrl, msg.sender, block.timestamp);
    }

    /**
     * @notice Verify that a fingerprint matches an on-chain record.
     * @param _fingerprint The SHA-256 fingerprint to verify
     * @return True if the fingerprint is registered on-chain
     */
    function verifyRecord(bytes32 _fingerprint) external view returns (bool) {
        return fingerprintExists[_fingerprint];
    }

    /**
     * @notice Get a full record by record ID.
     */
    function getRecord(uint256 recordId) external view returns (
        bytes32 fingerprint,
        bytes32 contentId,
        string memory sourceUrl,
        uint256 timestamp,
        address submitter,
        bool isRegistered
    ) {
        require(recordId < recordCount, "Record out of bounds");
        Record memory r = records[recordId];
        return (r.fingerprint, r.contentId, r.sourceUrl, r.timestamp, r.submitter, r.isRegistered);
    }

    /**
     * @notice Get the record ID for a given fingerprint.
     */
    function getRecordIdByFingerprint(bytes32 _fingerprint) external view returns (uint256) {
        return fingerprintToRecordId[_fingerprint];
    }
}
