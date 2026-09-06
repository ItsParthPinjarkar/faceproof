import os, json, sys, logging
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from app.pipeline import Pipeline, run_pipeline

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("faceproof-api")

FACE_DIR = Path(__file__).parent / "demo"
FACE_DIR.mkdir(exist_ok=True)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/api/faceproof/predict", methods=["POST"])
def predict():
    """Run the FaceProof pipeline on an uploaded image."""
    try:
        image_path = None
        if "image" in request.files:
            f = request.files["image"]
            ext = os.path.splitext(f.filename)[1].lower() or ".jpg"
            image_path = str(FACE_DIR / f"upload_{os.getpid()}{ext}")
            f.save(image_path)
        else:
            image_path = request.json.get("image_path") if request.json else None

        if not image_path or not os.path.exists(image_path):
            return jsonify({"error": "Image not found"}), 400

        logger.info(f"Running pipeline with: {image_path}")
        pipeline = Pipeline()
        result = pipeline.run(image_path)

        result_dict = {
            "face_hash": result.face_hash,
            "face_encoding_dim": result.face_encoding_dim,
            "face_details": result.face_details,
            "source_url": result.source_url,
            "platform": result.platform,
            "title": result.title,
            "fingerprint": result.fingerprint,
            "content_id": result.content_id,
            "ipfs_uri": result.ipfs_uri,
            "storage_type": result.storage_type,
            "tx_hash": result.tx_hash,
            "block_number": result.block_number,
            "gas_used": result.gas_used,
            "verification": result.verification,
            "etherscan_url": result.etherscan_url,
            "record_id": result.record_id,
            "demo_mode": result.demo_mode,
            "error": result.error,
        }

        return jsonify(result_dict)
    except Exception as e:
        logger.exception("Pipeline error")
        return jsonify({"error": str(e)}), 500
    finally:
        if image_path and os.path.exists(image_path) and "upload_" in os.path.basename(image_path):
            try:
                os.unlink(image_path)
            except OSError:
                pass

@app.route("/api/faceproof/verify", methods=["POST"])
def verify():
    """Verify a fingerprint on the blockchain."""
    try:
        data = request.json
        fingerprint = data.get("fingerprint")
        if not fingerprint:
            return jsonify({"error": "fingerprint required"}), 400

        rpc_url = os.environ.get("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        private_key = os.environ.get("BLOCKCHAIN_PRIVATE_KEY", "")
        contract_addr = os.environ.get("CONTRACT_ADDRESS", "")
        chain_id = int(os.environ.get("BLOCKCHAIN_CHAIN_ID", "31337"))

        from app.blockchain import BlockchainClient
        client = BlockchainClient(rpc_url, private_key, contract_addr, chain_id)
        verified = client.verify_fingerprint(fingerprint)
        count = client.get_record_count()
        record_id = client.get_record_id_by_fingerprint(fingerprint)

        return jsonify({
            "verified": verified,
            "record_count": count,
            "record_id": record_id,
        })
    except Exception as e:
        logger.exception("Verification error")
        return jsonify({"error": str(e)}), 500

@app.route("/api/faceproof/status", methods=["GET"])
def status():
    """Check blockchain connectivity and contract status."""
    try:
        rpc_url = os.environ.get("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        connected = w3.is_connected()
        chain_id = w3.eth.chain_id if connected else None
        accounts = len(w3.eth.accounts) if connected else 0

        contract_addr = os.environ.get("CONTRACT_ADDRESS", "")
        contract_deployed = False
        if connected and contract_addr:
            code = w3.eth.get_code(contract_addr)
            contract_deployed = len(code) > 0

        return jsonify({
            "connected": connected,
            "chain_id": chain_id,
            "accounts": accounts,
            "contract_deployed": contract_deployed,
            "contract_address": contract_addr,
        })
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 200

@app.route("/api/faceproof/demo-images", methods=["GET"])
def demo_images():
    """List available demo images."""
    try:
        images = []
        if FACE_DIR.exists():
            for f in sorted(FACE_DIR.glob("*")):
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    images.append(f.name)
        return jsonify({"images": images})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/faceproof/demo-images/<filename>", methods=["GET"])
def demo_image(filename):
    """Serve a demo image."""
    try:
        path = FACE_DIR / filename
        if not path.exists() or path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            return jsonify({"error": "Image not found"}), 404
        return send_file(str(path), mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/faceproof/predict-demo", methods=["POST"])
def predict_demo():
    """Run pipeline with the demo test_face.jpg image."""
    try:
        demo_path = str(FACE_DIR / "test_face.jpg")
        if not os.path.exists(demo_path):
            return jsonify({"error": "Demo image not found"}), 404
        logger.info(f"Running pipeline with demo: {demo_path}")
        pipeline = Pipeline()
        result = pipeline.run(demo_path)
        result_dict = {
            "face_hash": result.face_hash,
            "face_encoding_dim": result.face_encoding_dim,
            "face_details": result.face_details,
            "source_url": result.source_url,
            "platform": result.platform,
            "title": result.title,
            "fingerprint": result.fingerprint,
            "content_id": result.content_id,
            "ipfs_uri": result.ipfs_uri,
            "storage_type": result.storage_type,
            "tx_hash": result.tx_hash,
            "block_number": result.block_number,
            "gas_used": result.gas_used,
            "verification": result.verification,
            "etherscan_url": result.etherscan_url,
            "record_id": result.record_id,
            "demo_mode": result.demo_mode,
            "error": result.error,
        }
        return jsonify(result_dict)
    except Exception as e:
        logger.exception("Demo pipeline error")
        return jsonify({"error": str(e)}), 500

@app.route("/api/faceproof/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "FaceProof"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("API_PORT", 5000)))
    logger.info(f"Starting FaceProof API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)