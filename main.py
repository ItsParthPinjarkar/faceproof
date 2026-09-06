import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

from app.pipeline import Pipeline, run_pipeline


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_face_photo.jpg>")
        print("Set SERPAPI_KEY, BLOCKCHAIN_RPC_URL, BLOCKCHAIN_PRIVATE_KEY, CONTRACT_ADDRESS in .env")
        print("Set DEMO_MODE=true for demo mode without API keys")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    logger.info(f"Starting pipeline with: {image_path}")

    pipeline = Pipeline()
    result = pipeline.run(image_path)

    # Print summary
    print(result.get_summary())

    # Save results
    output_dir = os.environ.get('ARTIFACTS_DIR', 'artifacts')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'pipeline_result.json')

    result_dict = {
        'face_hash': result.face_hash,
        'face_encoding_dim': result.face_encoding_dim,
        'face_details': result.face_details,
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

    # Exit with error if pipeline failed
    if result.error:
        sys.exit(1)


if __name__ == '__main__':
    main()
