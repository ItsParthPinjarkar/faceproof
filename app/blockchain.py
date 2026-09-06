import os
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from web3 import Web3
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class BlockchainClient:
    """
    Web3.py client for Ethereum Sepolia (or any EVM chain).
    Registers and verifies content fingerprints on-chain.
    """

    def __init__(self, rpc_url: str, private_key: str, contract_address: str, chain_id: int = 11155111):
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.contract_address = contract_address
        self.chain_id = chain_id
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError(f"Could not connect to RPC at {rpc_url}")
        logger.info(f"Connected to blockchain (chain ID: {chain_id})")

        self.account = self.w3.eth.account.from_key(private_key)
        self.w3.eth.default_account = self.account.address

        # Contract ABI (matches ContentVerification.sol)
        self.contract_abi = [
            {"inputs":[{"internalType":"bytes32","name":"_fingerprint","type":"bytes32"},{"internalType":"bytes32","name":"_contentId","type":"bytes32"},{"internalType":"string","name":"_sourceUrl","type":"string"}],"name":"registerRecord","outputs":[],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[{"internalType":"bytes32","name":"_fingerprint","type":"bytes32"}],"name":"verifyRecord","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"uint256","name":"recordId","type":"uint256"}],"name":"getRecord","outputs":[{"internalType":"bytes32","name":"fingerprint","type":"bytes32"},{"internalType":"bytes32","name":"contentId","type":"bytes32"},{"internalType":"string","name":"sourceUrl","type":"string"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"address","name":"submitter","type":"address"},{"internalType":"bool","name":"isRegistered","type":"bool"}],"stateMutability":"view","type":"function"},
            {"inputs":[],"name":"recordCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"inputs":[{"internalType":"bytes32","name":"_fingerprint","type":"bytes32"}],"name":"getRecordIdByFingerprint","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
            {"anonymous":False,"inputs":[{"indexed":True,"internalType":"uint256","name":"recordId","type":"uint256"},{"indexed":True,"internalType":"bytes32","name":"fingerprint","type":"bytes32"},{"indexed":True,"internalType":"bytes32","name":"contentId","type":"bytes32"},{"indexed":False,"internalType":"string","name":"sourceUrl","type":"string"},{"indexed":False,"internalType":"address","name":"submitter","type":"address"},{"indexed":False,"internalType":"uint256","name":"timestamp","type":"uint256"}],"name":"RecordRegistered","type":"event"}
        ]
        self.contract = self.w3.eth.contract(address=contract_address, abi=self.contract_abi)

    @staticmethod
    def _to_bytes32(hex_str: str) -> bytes:
        """Normalize a hex string (with or without 0x) to 32 bytes."""
        h = hex_str[2:] if hex_str.startswith('0x') else hex_str
        return bytes.fromhex(h.zfill(64)[-64:])

    def register_record(self, fingerprint: str, content_id: str, source_url: str) -> dict:
        """
        Register a fingerprint on the blockchain.
        Returns transaction receipt info.
        """
        fp_bytes = self._to_bytes32(fingerprint)
        cid_bytes = self._to_bytes32(content_id)

        nonce = self.w3.eth.get_transaction_count(self.account.address)

        tx = self.contract.functions.registerRecord(
            fp_bytes,
            cid_bytes,
            source_url
        ).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'chainId': self.chain_id,
            'gas': 300000,
            'maxFeePerGas': self.w3.to_wei('20', 'gwei'),
            'maxPriorityFeePerGas': self.w3.to_wei('1', 'gwei'),
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"Transaction submitted: {tx_hash.hex()}")

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        logger.info(f"Transaction confirmed in block {receipt['blockNumber']}")

        return {
            'tx_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber'],
            'gas_used': receipt['gasUsed'],
            'contract_address': self.contract_address,
            'status': receipt['status'],
            'timestamp': datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }

    def verify_fingerprint(self, fingerprint: str) -> bool:
        """Verify a fingerprint exists on-chain."""
        result = self.contract.functions.verifyRecord(self._to_bytes32(fingerprint)).call()
        return bool(result)

    def get_record_id_by_fingerprint(self, fingerprint: str) -> Optional[int]:
        """Get the on-chain record ID for a fingerprint."""
        try:
            return int(self.contract.functions.getRecordIdByFingerprint(self._to_bytes32(fingerprint)).call())
        except Exception as e:
            logger.error(f"Failed to get record ID: {e}")
            return None

    def get_record(self, record_id: int) -> Optional[dict]:
        """Retrieve a record by ID from the blockchain."""
        try:
            record = self.contract.functions.getRecord(record_id).call()
            return {
                'fingerprint': record[0].hex() if isinstance(record[0], bytes) else str(record[0]),
                'content_id': record[1].hex() if isinstance(record[1], bytes) else str(record[1]),
                'source_url': record[2],
                'timestamp': record[3],
                'submitter': record[4],
                'is_registered': record[5]
            }
        except Exception as e:
            logger.error(f"Failed to get record: {e}")
            return None

    def get_record_count(self) -> int:
        """Get total number of registered records."""
        return int(self.contract.functions.recordCount().call())

    def get_etherscan_url(self, tx_hash: str) -> str:
        """Generate Etherscan URL for a transaction."""
        base = os.environ.get('BLOCK_EXPLORER_URL', 'https://etherscan.io')
        return f"{base}/tx/{tx_hash}"

    def get_contract_url(self) -> str:
        """Generate Etherscan URL for the contract."""
        base = os.environ.get('BLOCK_EXPLORER_URL', 'https://etherscan.io')
        return f"{base}/address/{self.contract_address}"


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if len(os.environ.get('CONTRACT_ADDRESS', '')) == 0:
        print("Set CONTRACT_ADDRESS in .env")
    else:
        client = BlockchainClient(
            os.environ['BLOCKCHAIN_RPC_URL'],
            os.environ['BLOCKCHAIN_PRIVATE_KEY'],
            os.environ['CONTRACT_ADDRESS'],
            int(os.environ.get('BLOCKCHAIN_CHAIN_ID', '11155111'))
        )
        count = client.get_record_count()
        print(f"Total records on-chain: {count}")
