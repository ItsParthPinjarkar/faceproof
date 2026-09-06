import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

from app.pipeline import Pipeline

def main():
    if len(sys.argv) < 2:
        image_path = 'demo/test_face.jpg'
    else:
        image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        print("Available images:")
        if os.path.exists('demo'):
            for f in os.listdir('demo'):
                print(f"  demo/{f}")
        sys.exit(1)

    print(f"Running pipeline with: {image_path}")
    print()

    pipeline = Pipeline()
    result = pipeline.run(image_path)

    # Print summary using ASCII only
    r = result
    summary_lines = [
        "",
        "=" * 60,
        "  FACE ID + BLOCKCHAIN PIPELINE SUMMARY",
        "=" * 60,
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
        summary_lines.append("  [!] RUNNING IN DEMO MODE - Results are labeled test data")
    if r.error:
        summary_lines.append(f"  [ERROR] {r.error}")

    print("\n".join(summary_lines))

    # Save results
    output_dir = 'artifacts'
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
    }

    with open(output_file, 'w') as f:
        json.dump(result_dict, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")

if __name__ == '__main__':
    main()
