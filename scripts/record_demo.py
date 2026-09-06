"""
Demo screen recording runner.
Creates a polished evidence video from a pipeline run.
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def record_demo():
    """Run pipeline and generate demo video artifacts."""
    from app.pipeline import Pipeline, run_pipeline

    demo_image = sys.argv[1] if len(sys.argv) > 1 else 'demo/subject1.jpg'

    if not os.path.exists(demo_image):
        print(f"Image not found: {demo_image}")
        print("Run: python scripts/make_demo_data.py")
        sys.exit(1)

    pipeline = Pipeline()
    result = pipeline.run(demo_image)

    print(result.get_summary())

    # Save output for video generation
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    with open(f'{output_dir}/pipeline_run.json', 'w') as f:
        json.dump({
            'face_hash': result.face_hash,
            'source_url': result.source_url,
            'platform': result.platform,
            'fingerprint': result.fingerprint,
            'tx_hash': result.tx_hash,
            'verification': result.verification,
            'demo_mode': result.demo_mode,
            'evidence_record': result.evidence_record,
            'canonical_json': result.canonical_json
        }, f, indent=2, default=str)

    print(f"\nPipeline output saved to {output_dir}/pipeline_run.json")
    print("Generate video with: ffmpeg -i demo_video_input.mp4 -c:v libx264 output.mp4")
    print("Or use the CLI recording script.")

if __name__ == '__main__':
    record_demo()
