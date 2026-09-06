import base64
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class IPFSClient:
    """
    IPFS client for decentralized evidence storage.
    Pins content to IPFS and returns a CID.
    """

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.environ.get('IPFS_API_URL', 'https://api.pinata.cloud')
        self.api_key = api_key or os.environ.get('IPFS_PINNING_KEY', '')
        self._fallback_gateway = 'https://ipfs.io/ipfs/'

    def pin_json(self, data: dict) -> Optional[str]:
        """
        Upload JSON data to IPFS and return the CID.
        Returns None if IPFS is not configured.
        """
        if not self.api_url or not self.api_key:
            logger.info("IPFS not configured; returning data URI instead")
            return None

        try:
            import requests
            json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))

            resp = requests.post(
                f'{self.api_url}/pinning/pinJSONToIPFS',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'pinataContent': {'evidence': data},
                    'pinataOptions': {'cidVersion': 1}
                },
                timeout=30
            )

            if resp.status_code == 200:
                cid = resp.json()['IpfsHash']
                logger.info(f"Pinned to IPFS: {self._fallback_gateway}{cid}")
                return cid
            else:
                logger.warning(f"IPFS pin failed: {resp.status_code}")
        except Exception as e:
            logger.warning(f"IPFS upload failed: {e}")

        return None

    def get_gateway_url(self, cid: str) -> str:
        """Get the full gateway URL for an IPFS CID."""
        return f"{self._fallback_gateway}{cid}"

    def create_data_uri(self, data: dict) -> str:
        """Create a data:application/json URI as fallback."""
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return f"data:application/json;base64,{base64.b64encode(json_str.encode()).decode()}"

    def store_evidence(self, evidence: dict) -> dict:
        """
        Store evidence on IPFS (if configured) or create a data URI.
        Returns dict with 'storage_type', 'uri', and 'cid'.
        """
        import base64

        # Try IPFS first
        cid = self.pin_json(evidence)
        if cid:
            return {
                'storage_type': 'ipfs',
                'cid': cid,
                'uri': self.get_gateway_url(cid)
            }

        # Fallback: data URI
        data_uri = self.create_data_uri(evidence)
        return {
            'storage_type': 'data_uri',
            'cid': None,
            'uri': data_uri
        }


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    client = IPFSClient()
    test = {'test': 'data'}
    result = client.store_evidence(test)
    print(f"Storage result: {result}")
