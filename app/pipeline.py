import os
import json
import logging
import sys
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment early
load_dotenv()

from app.face import FaceEngine
from app.search import create_provider, SearchProvider
from app.hashing import canonicalize, sha256_hash, keccak256_hash, make_evidence_record, compute_fingerprint
from app.blockchain import BlockchainClient
from app.ipfs import IPFSClient

logger = logging.getLogger(__name__)


class PipelineResult:
    """Container for the complete pipeline result."""
    def __init__(self):
        self.stage = None
        self.face_hash = None
        self.face_encoding_dim = None
        self.face_details = None
        self.search_results = []
        self.best_match = None
        self.platform = None
        self.source_url = None
        self.title = None
        self.evidence_record = None
        self.canonical_json = None
        self.fingerprint = None
        self.content_id = None
        self.ipfs_uri = None
        self.ipfs_cid = None
        self.storage_type = None
        self.tx_hash = None
        self.block_number = None
        self.gas_used = None
        self.verification = None
        self.etherscan_url = None
        self.record_id = None
        self.error = None
        self.demo_mode = False

    def get_summary(self) -> str:
        """Get a human-readable summary of the pipeline result (ASCII-safe for Windows consoles)."""
        r = self
        lines = [
            "",
            "=" * 62,
            "            FACE ID + BLOCKCHAIN PIPELINE SUMMARY",
            "=" * 62,
            "",
            f"  Face Hash:          {r.face_hash[:16] + '...' if r.face_hash else 'N/A'}",
            f"  Encoding Dimensions: {r.face_encoding_dim or 'N/A'}",
            f"  Source URL:         {r.source_url[:50] + '...' if r.source_url else 'N/A'}",
            f"  Platform:           {r.platform or 'N/A'}",
            f"  Title:              {r.title[:50] + '...' if r.title else 'N/A'}",
            f"  Fingerprint:        {r.fingerprint[:16] + '...' if r.fingerprint else 'N/A'}",
            f"  IPFS URI:           {r.ipfs_uri[:50] + '...' if r.ipfs_uri else 'N/A'}",
            f"  Storage Type:       {r.storage_type or 'N/A'}",
            f"  Transaction Hash:   {r.tx_hash[:16] + '...' if r.tx_hash else 'N/A'}",
            f"  Block Number:       {r.block_number}",
            f"  Gas Used:           {r.gas_used}",
            f"  Verification:       {r.verification or 'N/A'}",
            f"  Etherscan:          {r.etherscan_url or 'N/A'}",
            f"  Record ID:          {r.record_id}",
            f"  Demo Mode:          {r.demo_mode}",
            "",
        ]
        if r.demo_mode:
            lines.append("  [!] RUNNING IN DEMO MODE - Results are labeled test data")
        if r.error:
            lines.append(f"  [ERROR] {r.error}")

        return "\n".join(lines)


class Pipeline:
    """
    Main pipeline orchestrator.
    Executes: FACE → SEARCH → MATCH → FINGERPRINT → BLOCKCHAIN → VERIFY
    """

    def __init__(self):
        self.result = PipelineResult()
        self.face_engine = FaceEngine()
        self.provider_name = os.environ.get('SEARCH_PROVIDER', 'serpapi')
        self.demo_mode = os.environ.get('DEMO_MODE', 'false').lower() == 'true'

        # Create search provider
        if self.provider_name == 'demo' or self.demo_mode:
            self.search_provider = create_provider('demo')
            self.result.demo_mode = True
        else:
            self.search_provider = create_provider(
                self.provider_name,
                api_key=os.environ.get('SERPAPI_KEY', '')
            )

        # Create blockchain client if configured
        self.blockchain_client = None
        if all([
            os.environ.get('BLOCKCHAIN_RPC_URL'),
            os.environ.get('BLOCKCHAIN_PRIVATE_KEY'),
            os.environ.get('CONTRACT_ADDRESS')
        ]):
            try:
                self.blockchain_client = BlockchainClient(
                    rpc_url=os.environ['BLOCKCHAIN_RPC_URL'],
                    private_key=os.environ['BLOCKCHAIN_PRIVATE_KEY'],
                    contract_address=os.environ['CONTRACT_ADDRESS'],
                    chain_id=int(os.environ.get('BLOCKCHAIN_CHAIN_ID', '11155111'))
                )
            except ConnectionError:
                logger.warning("Blockchain RPC not available. Running without blockchain.")
                self.blockchain_client = None

        # Create IPFS client
        self.ipfs_client = IPFSClient()

    def run(self, image_path: str) -> PipelineResult:
        """
        Execute the full pipeline end-to-end.
        Returns a PipelineResult with all stages populated.
        """
        if not os.path.exists(image_path):
            self.result.error = f"Image not found: {image_path}"
            return self.result

        try:
            # === STAGE 1: FACE DETECTION & ENCODING ===
            self._stage_face(image_path)

            if self.result.error:
                return self.result

            # === STAGE 2: REVERSE IMAGE SEARCH ===
            self._stage_search(image_path)

            if not self.result.best_match:
                self.result.error = "No search results found"
                return self.result

            # === STAGE 3: CONTENT PROOF ===
            self._stage_fingerprint()

            # === STAGE 4: BLOCKCHAIN REGISTRATION ===
            self._stage_blockchain()

            # === STAGE 5: VERIFICATION ===
            self._stage_verify()

        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            self.result.error = str(e)

        return self.result

    def _stage_face(self, image_path: str):
        """Stage 1: Detect face and compute encoding + hash."""
        logger.info("=" * 60)
        logger.info("[1/5] FACE DETECTION & ENCODING")
        logger.info("=" * 60)

        face = self.face_engine.detect_primary_face(image_path)
        face_hash = self.face_engine.compute_face_hash(face)

        self.result.face_hash = face_hash
        self.result.face_encoding_dim = len(face['encoding'])
        self.result.face_details = {
            'bbox': face.get('bbox'),
            'gender': face.get('gender'),
            'age': face.get('age'),
            'score': face.get('score')
        }

        logger.info(f"Face detected: hash={face_hash[:16]}..., dims={self.result.face_encoding_dim}")
        logger.info(f"Gender: {face.get('gender')}, Age: {face.get('age')}, Confidence: {float(face.get('score')):.2f}")

    def _stage_search(self, image_path: str):
        """Stage 2: Reverse image search via SerpAPI."""
        logger.info("=" * 60)
        logger.info("[2/5] REVERSE IMAGE SEARCH")
        logger.info("=" * 60)

        matches = self.search_provider.search(image_path)
        self.result.search_results = matches

        if not matches:
            logger.warning("No search results returned")
            return

        # Pick best social media match
        best = self._pick_best_match(matches)
        self.result.best_match = best
        self.result.platform = best.get('platform', best.get('domain', 'Unknown'))
        self.result.source_url = best.get('url', '')
        self.result.title = best.get('title', 'N/A')
        self.result.demo_mode = best.get('_is_demo', False)

        logger.info(f"Best match: {self.result.title}")
        logger.info(f"URL: {self.result.source_url}")
        logger.info(f"Platform: {self.result.platform}")
        logger.info(f"Match type: {best.get('match_type', 'visual_match')}")

    def _pick_best_match(self, matches: List[Dict]) -> Dict:
        """Pick the best match, preferring social media platforms."""
        social_keywords = ['instagram', 'twitter', 'x.com', 'facebook', 'reddit',
                          'tiktok', 'linkedin', 'tumblr', 'pinterest', 'medium',
                          'github', 'youtube']

        for match in matches:
            url = match.get('url', '').lower()
            if any(kw in url for kw in social_keywords):
                return match

        return matches[0] if matches else {}

    def _stage_fingerprint(self):
        """Stage 3: Build canonical evidence record and compute fingerprint."""
        logger.info("=" * 60)
        logger.info("[3/5] CONTENT PROOF (SHA-256 FINGERPRINT)")
        logger.info("=" * 60)

        evidence = make_evidence_record(
            face_hash=self.result.face_hash,
            source_url=self.result.source_url,
            title=self.result.title,
            domain=self.result.platform,
            snippet=self.result.best_match.get('snippet', ''),
            platform=self.result.platform,
            match_type=self.result.best_match.get('match_type', 'visual_match')
        )

        self.result.evidence_record = evidence

        # Store on IPFS
        ipfs_result = self.ipfs_client.store_evidence(evidence)
        self.result.ipfs_uri = ipfs_result['uri']
        self.result.ipfs_cid = ipfs_result['cid']
        self.result.storage_type = ipfs_result['storage_type']

        # Compute canonical JSON + fingerprint
        self.result.canonical_json, self.result.fingerprint, self.result.content_id = compute_fingerprint(evidence)

        logger.info(f"Canonical JSON (first 100 chars): {self.result.canonical_json[:100]}...")
        logger.info(f"SHA-256 Fingerprint: {self.result.fingerprint}")
        logger.info(f"Content ID (keccak256 of URL): {self.result.content_id}")
        logger.info(f"IPFS URI: {self.result.ipfs_uri[:80] if self.result.ipfs_uri else 'N/A'}")
        logger.info(f"Storage type: {self.result.storage_type}")

    def _stage_blockchain(self):
        """Stage 4: Register fingerprint on the blockchain."""
        logger.info("=" * 60)
        logger.info("[4/5] BLOCKCHAIN REGISTRATION")
        logger.info("=" * 60)

        if not self.blockchain_client:
            logger.warning("Blockchain not configured. Skipping on-chain registration.")
            self.result.error = "Blockchain not configured"
            return

        try:
            tx_result = self.blockchain_client.register_record(
                fingerprint=self.result.fingerprint,
                content_id=self.result.content_id,
                source_url=self.result.source_url
            )

            self.result.tx_hash = tx_result['tx_hash']
            self.result.block_number = tx_result['block_number']
            self.result.gas_used = tx_result['gas_used']
            self.result.etherscan_url = self.blockchain_client.get_etherscan_url(tx_result['tx_hash'])

            logger.info(f"Transaction hash: {tx_result['tx_hash'][:16]}...")
            logger.info(f"Block number: {tx_result['block_number']}")
            logger.info(f"Gas used: {tx_result['gas_used']}")
            logger.info(f"Etherscan: {self.result.etherscan_url}")

        except Exception as e:
            logger.error(f"Blockchain registration failed: {e}")
            self.result.error = f"Blockchain registration failed: {e}"

    def _stage_verify(self):
        """Stage 5: Re-verify the fingerprint against the blockchain."""
        logger.info("=" * 60)
        logger.info("[5/5] VERIFICATION")
        logger.info("=" * 60)

        if not self.blockchain_client:
            self.result.verification = 'SKIPPED_NO_CHAIN'
            return

        try:
            verified = self.blockchain_client.verify_fingerprint(self.result.fingerprint)
            self.result.verification = 'VERIFIED' if verified else 'TAMPERED'

            # Get record ID
            record_id = self.blockchain_client.get_record_id_by_fingerprint(self.result.fingerprint)
            self.result.record_id = record_id

            logger.info(f"Verification result: {self.result.verification}")
            logger.info(f"Record ID: {record_id}")

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            self.result.verification = 'ERROR'
            self.result.error = f"Verification error: {e}"

    def get_summary(self) -> str:
        """Get a human-readable summary of the pipeline result (ASCII-safe for Windows consoles)."""
        r = self.result
        lines = [
            "",
            "=" * 62,
            "            FACE ID + BLOCKCHAIN PIPELINE SUMMARY",
            "=" * 62,
            "",
            f"  Face Hash:          {r.face_hash[:16] + '...' if r.face_hash else 'N/A'}",
            f"  Encoding Dimensions: {r.face_encoding_dim}",
            f"  Source URL:         {r.source_url[:50] + '...' if r.source_url else 'N/A'}",
            f"  Platform:           {r.platform}",
            f"  Title:              {r.title[:50] + '...' if r.title else 'N/A'}",
            f"  Fingerprint:        {r.fingerprint[:16] + '...' if r.fingerprint else 'N/A'}",
            f"  IPFS URI:           {r.ipfs_uri[:50] + '...' if r.ipfs_uri else 'N/A'}",
            f"  Storage Type:       {r.storage_type or 'N/A'}",
            f"  Transaction Hash:   {r.tx_hash[:16] + '...' if r.tx_hash else 'N/A'}",
            f"  Block Number:       {r.block_number}",
            f"  Gas Used:           {r.gas_used}",
            f"  Verification:       {r.verification}",
            f"  Etherscan:          {r.etherscan_url or 'N/A'}",
            "",
        ]
        if r.demo_mode:
            lines.append("  [!] RUNNING IN DEMO MODE - Results are labeled test data")
        if r.error:
            lines.append(f"  [ERROR] {r.error}")

        return "\n".join(lines)


def run_pipeline(image_path: str) -> PipelineResult:
    """Convenience function to run the pipeline."""
    pipeline = Pipeline()
    return pipeline.run(image_path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    if len(sys.argv) < 2:
        print("Usage: python -m app.pipeline <path_to_face_photo.jpg>")
        sys.exit(1)

    result = run_pipeline(sys.argv[1])
    print(result.get_summary())

    # Save results to JSON
    output_dir = os.environ.get('ARTIFACTS_DIR', 'artifacts')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'pipeline_result.json')

    result_dict = {
        'face_hash': result.face_hash,
        'face_encoding_dim': result.face_encoding_dim,
        'source_url': result.source_url,
        'platform': result.platform,
        'title': result.title,
        'fingerprint': result.fingerprint,
        'content_id': result.content_id,
        'ipfs_uri': result.ipfs_uri,
        'storage_type': result.storage_type,
        'tx_hash': result.tx_hash,
        'block_number': result.block_number,
        'gas_used': result.gas_used,
        'verification': result.verification,
        'etherscan_url': result.etherscan_url,
        'record_id': result.record_id,
        'demo_mode': result.demo_mode,
        'error': result.error,
        'evidence_record': result.evidence_record,
        'canonical_json': result.canonical_json
    }

    with open(output_file, 'w') as f:
        json.dump(result_dict, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")
