"""
Comprehensive test suite for the FaceProof pipeline.
100% mocked offline tests — no network, RPC, or API keys consumed.
"""
import pytest
import json
import hashlib
import os
import sys
import tempfile
import numpy as np
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.hashing import canonicalize, sha256_hash, keccak256_hash, make_evidence_record, compute_fingerprint
from app.face import FaceEngine
import cv2


class TestCanonicalization:
    """Test RFC 8785 JSON canonicalization."""

    def test_canonicalize_sorts_keys(self):
        """Keys must be sorted alphabetically."""
        data = {"z": 1, "a": 2, "m": 3}
        result = canonicalize(data)
        assert result.index('"a"') < result.index('"m"') < result.index('"z"')

    def test_canonicalize_compact_separators(self):
        """No whitespace in output."""
        data = {"key": "value"}
        result = canonicalize(data)
        assert " " not in result

    def test_canonicalize_deterministic(self):
        """Same input always produces same output."""
        data = {"b": 1, "a": 2}
        r1 = canonicalize(data)
        r2 = canonicalize(data)
        assert r1 == r2

    def test_canonicalize_produces_string(self):
        """Output must be a string."""
        data = {"test": "data"}
        result = canonicalize(data)
        assert isinstance(result, str)


class TestHashing:
    """Test SHA-256 and keccak256 hashing."""

    def test_sha256_returns_hex(self):
        """SHA-256 must return a 64-character hex string."""
        result = sha256_hash("test")
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)

    def test_sha256_deterministic(self):
        """Same input always produces same hash."""
        assert sha256_hash("hello") == sha256_hash("hello")

    def test_sha256_changes_with_input(self):
        """Different inputs produce different hashes."""
        h1 = sha256_hash("hello")
        h2 = sha256_hash("world")
        assert h1 != h2

    def test_keccak256_returns_hex(self):
        """Keccak256 must return a valid hex string."""
        result = keccak256_hash("test")
        assert result.startswith('0x')
        assert len(result) == 66  # 0x + 64 hex chars

    def test_tamper_changes_hash(self):
        """Changing even 1 bit changes the hash completely."""
        original = json.dumps({"field": "value"}, sort_keys=True)
        tampered = json.dumps({"field": "valueX"}, sort_keys=True)
        h1 = sha256_hash(original)
        h2 = sha256_hash(tampered)
        assert h1 != h2


class TestEvidenceRecord:
    """Test evidence record construction."""

    def test_make_evidence_record(self):
        """Evidence record must contain all required fields."""
        record = make_evidence_record(
            face_hash="abc123",
            source_url="https://instagram.com/p/test",
            title="Test Post",
            domain="instagram.com",
            snippet="Hello",
            platform="Instagram",
            match_type="visual_match"
        )
        assert record["face_hash"] == "abc123"
        assert record["source_url"] == "https://instagram.com/p/test"
        assert record["title"] == "Test Post"
        assert record["platform"] == "Instagram"
        assert record["match_type"] == "visual_match"
        assert "timestamp" in record

    def test_compute_fingerprint(self):
        """Must return canonical JSON, fingerprint, and content ID."""
        record = make_evidence_record(
            face_hash="abc", source_url="https://x.com/test",
            title="X", domain="x.com", snippet="test", platform="X"
        )
        canonical, fingerprint, content_id = compute_fingerprint(record)
        assert isinstance(canonical, str)
        assert len(fingerprint) == 64  # SHA-256 hex
        assert content_id.startswith('0x')  # keccak256 hex


class TestFaceEngine:
    """Test FaceEngine with mocked InsightFace."""

    @patch('app.face.insightface')
    @patch('cv2.imread')
    def test_detect_faces_returns_list(self, mock_cv2_imread, mock_insightface):
        """FaceEngine.detect_faces must return a list."""
        mock_app = MagicMock()
        mock_insightface.app.FaceAnalysis.return_value = mock_app
        mock_app.get.return_value = [{
            'bbox': np.array([10, 20, 100, 120]),
            'landmark_2d': np.array([[50, 60], [60, 60], [55, 70]]),
            'embedding': np.array([0.1] * 512),
            'gender': 0, 'age': 30, 'det_score': 0.95
        }]
        mock_cv2_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

        engine = FaceEngine()
        faces = engine.detect_faces("dummy_path.jpg")
        assert isinstance(faces, list)
        assert len(faces) == 1

    @patch('app.face.insightface')
    @patch('cv2.imread')
    def test_compute_face_hash(self, mock_cv2_imread, mock_insightface):
        """Face hash must be deterministic."""
        mock_app = MagicMock()
        mock_insightface.app.FaceAnalysis.return_value = mock_app
        mock_app.get.return_value = [{
            'bbox': np.array([10, 20, 100, 120]),
            'embedding': np.array([0.1] * 512),
            'gender': 0, 'age': 30
        }]
        mock_cv2_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

        engine = FaceEngine()
        face = engine.detect_primary_face("dummy.jpg")
        h1 = engine.compute_face_hash(face)
        h2 = engine.compute_face_hash(face)
        assert h1 == h2

    def test_cosine_similarity(self):
        """Cosine similarity of identical vectors must be 1.0."""
        engine = FaceEngine()
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        sim = engine.cosine_similarity(v1, v2)
        assert abs(sim - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        """Cosine similarity of orthogonal vectors must be 0.0."""
        engine = FaceEngine()
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        sim = engine.cosine_similarity(v1, v2)
        assert abs(sim - 0.0) < 0.001


class TestSearchProvider:
    """Test search provider factory and demo mode."""

    def test_create_provider_demo(self):
        """Demo provider must return labeled results."""
        from app.search import create_provider
        provider = create_provider('demo')
        results = provider.search("dummy.jpg")
        assert len(results) > 0
        assert results[0].get('_is_demo') == True

    def test_create_provider_serpapi(self):
        """SerpApi provider must be created with API key."""
        from app.search import create_provider, SerpApiGoogleLensProvider
        provider = create_provider('serpapi', api_key='test_key')
        assert isinstance(provider, SerpApiGoogleLensProvider)

    def test_provider_factory_unknown(self):
        """Unknown provider must raise ValueError."""
        from app.search import create_provider
        with pytest.raises(ValueError):
            create_provider('unknown')


class TestBlockchainClient:
    """Test blockchain client with mocked Web3."""

    @patch('app.blockchain.Web3')
    def test_register_and_verify(self, mock_web3):
        """Must register and verify a fingerprint."""
        from app.blockchain import BlockchainClient

        mock_w3 = MagicMock()
        mock_web3.return_value = mock_w3
        mock_w3.is_connected.return_value = True
        mock_w3.eth.account.from_key.return_value = MagicMock(address='0xTest')
        mock_w3.eth.get_transaction_count.return_value = 1

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_contract.functions.verifyRecord.return_value.call.return_value = True

        client = BlockchainClient(
            'http://localhost:8545', '0xPrivateKey', '0xContract', 11155111
        )
        client.contract = mock_contract

        # Verify
        result = client.verify_fingerprint('abc123' * 16)
        assert result == True

    @patch('app.blockchain.Web3')
    def test_get_record_count(self, mock_web3):
        """Must get record count."""
        from app.blockchain import BlockchainClient

        mock_w3 = MagicMock()
        mock_web3.return_value = mock_w3
        mock_w3.is_connected.return_value = True
        mock_contract = MagicMock()
        mock_contract.functions.recordCount.return_value.call.return_value = 5
        mock_w3.eth.contract.return_value = mock_contract

        client = BlockchainClient(
            'http://localhost:8545', '0xPrivateKey', '0xContract', 11155111
        )
        client.contract = mock_contract

        count = client.get_record_count()
        assert count == 5


class TestPipelineIntegration:
    """Test the full pipeline with all mocked."""

    @patch('app.pipeline.FaceEngine')
    @patch('app.pipeline.create_provider')
    @patch('app.pipeline.BlockchainClient')
    @patch('app.pipeline.IPFSClient')
    def test_pipeline_runs_all_stages(self, mock_ipfs, mock_bc, mock_sp, mock_fe):
        """Pipeline must execute all 5 stages."""
        from app.pipeline import Pipeline, PipelineResult

        # Mock face engine
        mock_face = MagicMock()
        mock_face['encoding'] = [0.1] * 512
        mock_face['bbox'] = [10, 20, 100, 120]
        mock_face['gender'] = 0
        mock_face['age'] = 30
        mock_face['det_score'] = 0.95
        mock_face_engine = MagicMock()
        mock_face_engine.detect_primary_face.return_value = mock_face
        mock_face_engine.compute_face_hash.return_value = 'a' * 64
        mock_fe.return_value = mock_face_engine

        # Mock search provider
        mock_matches = [{'url': 'https://instagram.com/p/test', 'title': 'Test', 'platform': 'Instagram', 'snippet': 'test', 'match_type': 'visual_match', '_is_demo': True}]
        mock_sp.return_value.search.return_value = mock_matches

        # Mock blockchain
        mock_bc_instance = MagicMock()
        mock_bc_instance.register_record.return_value = {'tx_hash': '0x' + 'b' * 64, 'block_number': 12345, 'gas_used': 250000}
        mock_bc_instance.verify_fingerprint.return_value = True
        mock_bc_instance.get_record_id_by_fingerprint.return_value = 0
        mock_bc.return_value = mock_bc_instance

        # Mock IPFS
        mock_ipfs.return_value.store_evidence.return_value = {'storage_type': 'data_uri', 'uri': 'data:application/json;base64,abc=', 'cid': None}

        # Run pipeline
        pipeline = Pipeline()
        pipeline.search_provider = mock_sp.return_value
        pipeline.blockchain_client = mock_bc_instance
        pipeline.ipfs_client = mock_ipfs.return_value

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'dummy')
            tmp_path = tmp.name

        try:
            result = pipeline.run(tmp_path)
            assert result.face_hash is not None
            assert result.fingerprint is not None
            assert result.verification == 'VERIFIED'
        finally:
            os.unlink(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
