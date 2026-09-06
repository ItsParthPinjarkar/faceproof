"""
Streamlit web dashboard for the FaceProof pipeline.
Provides drag-and-drop upload and live pipeline visualization.
"""
import streamlit as st
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="FaceProof — Face ID + Blockchain", layout="wide")


def main():
    st.title("🔍 FaceProof — Face ID + Blockchain Verification")
    st.markdown("**HH Goa 2026 Task 3** — Detect → Search → Finger-print → Anchor → Verify")

    # Upload face image
    uploaded_file = st.file_uploader(
        "Upload a face photo",
        type=['jpg', 'jpeg', 'png', 'webp'],
        help="Upload a consenting test image"
    )

    if uploaded_file:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Display image
        st.image(uploaded_file, caption="Uploaded face image", width=300)

        if st.button("🚀 Run Full Pipeline", type="primary"):
            with st.spinner("Running pipeline..."):
                run_pipeline_ui(tmp_path)

        # Cleanup
        os.unlink(tmp_path)

    # Pipeline status
    st.sidebar.title("Pipeline Status")
    st.sidebar.info("Steps: 1) Face → 2) Search → 3) Fingerprint → 4) Blockchain → 5) Verify")

    # Demo mode toggle
    st.sidebar.checkbox("Demo Mode (no API keys needed)", key="demo_mode")


def run_pipeline_ui(image_path: str):
    """Run the pipeline and display results."""
    from app.pipeline import Pipeline, PipelineResult

    pipeline = Pipeline()

    # Override demo mode if set
    if pipeline.demo_mode:
        st.warning("⚠️ Running in DEMO MODE — using labeled test data")

    result = pipeline.run(image_path)

    # Display results
    st.subheader("📊 Pipeline Results")

    cols = st.columns(2)
    with cols[0]:
        st.metric("Face Hash", result.face_hash[:16] + "..." if result.face_hash else "N/A")
        st.metric("Encoding Dimensions", result.face_encoding_dim or "N/A")
        st.metric("Platform", result.platform or "N/A")

    with cols[1]:
        st.metric("Fingerprint", result.fingerprint[:16] + "..." if result.fingerprint else "N/A")
        st.metric("Verification", result.verification or "N/A")
        st.metric("Storage Type", result.storage_type or "N/A")

    # Source info
    if result.source_url:
        st.markdown(f"**Source URL:** [⬆️ {result.source_url[:60]}...]({result.source_url})")
    if result.title:
        st.markdown(f"**Title:** {result.title}")

    # Transaction info
    if result.tx_hash:
        st.markdown(f"**Transaction:** `{result.tx_hash[:20]}...`")
        if result.etherscan_url:
            st.markdown(f"**Etherscan:** [⬆️ View on Explorer]({result.etherscan_url})")

    # Verification badge
    verification_color = {
        'VERIFIED': '🟢',
        'TAMPERED': '🔴',
        'ERROR': '🟠',
        'SKIPPED_NO_CHAIN': '🟡',
        'N/A': '⚪'
    }
    color = verification_color.get(result.verification, '⚪')
    st.markdown(f"### {color} **{result.verification}**")

    # Evidence record
    if result.evidence_record:
        with st.expander("📋 Evidence Record"):
            st.json(result.evidence_record)

    if result.canonical_json:
        with st.expander("📜 Canonical JSON (first 500 chars)"):
            st.code(result.canonical_json[:500])

    # Tamper demo
    if result.verification == 'VERIFIED':
        st.markdown("---")
        st.subheader("🛡️ Tamper Test")
        st.markdown("Click to simulate tampering and see verification fail:")

        if st.button("💥 Simulate Tampering"):
            st.info("Tampering detected — the fingerprint would change completely!")
            st.code("Original:  SHA-256(evidence) = a1b2c3...\nTampered:  SHA-256(evidence+1bit) = x9y8z7...\nOn-chain:  a1b2c3...\n→ MISMATCH → TAMPERED")


if __name__ == '__main__':
    main()
