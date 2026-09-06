import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def canonicalize(data: dict) -> str:
    """
    RFC 8785 JSON Canonicalization Scheme (JCS) canonicalization.
    Produces deterministic UTF-8 JSON with sorted keys and compact separators.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def sha256_hash(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def keccak256_hash(data: str) -> str:
    """Compute Keccak-256 hash of a string."""
    try:
        from web3 import Web3
        return '0x' + Web3.keccak(text=data).hex()
    except ImportError:
        # Fallback: use pycryptodome if web3 not available
        from Crypto.Hash import keccak as keccak_module
        k = keccak_module.new(digest_bits=256)
        k.update(data.encode('utf-8'))
        return '0x' + k.hexdigest()


def make_evidence_record(
    face_hash: str,
    source_url: str,
    title: str,
    domain: str,
    snippet: str,
    platform: str,
    match_type: str = "visual_match"
) -> dict:
    """
    Build the canonical evidence record dict.
    """
    record = {
        "face_hash": face_hash,
        "source_url": source_url,
        "title": title.strip(),
        "domain": domain,
        "snippet": snippet.strip(),
        "platform": platform,
        "match_type": match_type,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    return record


def compute_fingerprint(evidence_record: dict) -> tuple:
    """
    Compute the canonical JSON, SHA-256 fingerprint, and content ID.
    Returns (canonical_json_string, fingerprint_hex, content_id_hex).
    """
    canonical = canonicalize(evidence_record)
    fingerprint = sha256_hash(canonical)
    content_id = keccak256_hash(evidence_record["source_url"])
    return canonical, fingerprint, content_id


if __name__ == '__main__':
    # Demo
    test_record = {
        "face_hash": "abc123",
        "source_url": "https://instagram.com/p/test",
        "title": "Test Post",
        "domain": "instagram.com",
        "snippet": "Hello world",
        "platform": "Instagram",
        "match_type": "visual_match",
        "timestamp": "2026-01-01T00:00:00Z"
    }
    canonical, fp, cid = compute_fingerprint(test_record)
    print(f"Canonical: {canonical[:80]}...")
    print(f"Fingerprint: {fp}")
    print(f"Content ID: {cid}")
