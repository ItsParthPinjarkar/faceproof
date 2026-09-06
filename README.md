# FaceProof — Face ID + Blockchain Verification Pipeline

> **HH Goa 2026 Shortlisting Task 3**  
> An end-to-end decentralized identity pipeline: **FACE → SEARCH → MATCH → FINGERPRINT → BLOCKCHAIN → VERIFY**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![Solidity 0.8.24](https://img.shields.io/badge/Solidity-0.8.24-purple)]()
[![Ethereum Sepolia](https://img.shields.io/badge/Blockchain-Ethereum%20Sepolia-orange)]()
[![InsightFace buffalo_l](https://img.shields.io/badge/Face-InsightFace%20buffalo_l-green)]()
[![MIT License](https://img.shields.io/badge/License-MIT-yellow)]()

---

## 🎯 What It Does

1. **Face Detection & Encoding** — Detects the primary face in an image using **InsightFace buffalo_l** (ArcFace, LFW 99.83% accuracy, 512-D embedding). Computes a deterministic SHA-256 face hash.
2. **Genuine Reverse-Image Search** — Uses **SerpApi's Google Lens** engine (with proper Image API upload → image_id → Lens query flow). Falls back to **demo mode** with labeled test data. Never hardcodes results.
3. **Cryptographic Fingerprint** — Builds an RFC 8785 canonical JSON manifest from the matched evidence, computes **SHA-256 fingerprint** + **Keccak-256 content ID**. Stores evidence on **IPFS** (if configured) or creates a data URI.
4. **Blockchain Registration** — Registers the fingerprint on **Ethereum Sepolia** (or local Hardhat) via the `ContentVerification` smart contract with OpenZeppelin access control.
5. **Independent Verification** — Re-computes the fingerprint and compares against the on-chain record → **VERIFIED** or **TAMPERED**. Includes a one-click tamper simulation demo.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT IMAGE                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  1. FACE ENGINE (InsightFace buffalo_l)                  │
│     ├── Detect face + bounding box + landmarks           │
│     ├── Generate 512-D ArcFace embedding                 │
│     └── Compute SHA-256 face hash                        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  2. SEARCH ENGINE (SerpApi Google Lens)                  │
│     ├── Upload image → get image_id                      │
│     ├── Query Google Lens with image_id                  │
│     ├── Normalize results (social media prioritized)     │
│     └── Fallback: Demo mode with labeled data            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  3. EVIDENCE PROOF (RFC 8785 Canonical JSON)             │
│     ├── Build canonical record dict                      │
│     ├── Serialize with sorted keys, compact separators   │
│     ├── SHA-256 fingerprint + Keccak-256 content ID      │
│     ├── Pin evidence to IPFS (optional)                  │
│     └── Create data URI fallback                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  4. BLOCKCHAIN (Ethereum Sepolia / Hardhat)              │
│     ├── Deploy ContentVerification.sol                   │
│     ├── registerRecord(fingerprint, contentId, url)      │
│     ├── EIP-1559 transaction with access control         │
│     └── Emit RecordRegistered event                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  5. VERIFICATION (Independent Re-check)                  │
│     ├── Re-compute SHA-256 from canonical JSON           │
│     ├── Query blockchain: verifyRecord(fingerprint)      │
│     ├── Compare: VERIFIED / TAMPERED                     │
│     └── Tamper simulation: change 1 bit → mismatch       │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### Option A: Docker (Everything at Once)
```bash
docker compose up --build
# Frontend → http://localhost:5173
# API docs → http://localhost:8000/docs
# Local chain → http://localhost:8545
```

### Option B: Manual Setup (3 Terminals)

**Terminal 1 — Local Blockchain:**
```bash
cd contracts
npm install
npx hardhat node  # keep running
```

**Terminal 2 — Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # edit with your keys
python scripts/make_demo_data.py
uvicorn app.main:app --reload
```

**Terminal 3 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Option C: CLI Direct
```bash
pip install -r requirements.txt
cp .env.example .env
# Set SERPAPI_KEY, BLOCKCHAIN_RPC_URL, etc.
python scripts/make_demo_data.py
python main.py demo/subject1.jpg
```

### Option D: Streamlit Dashboard
```bash
pip install streamlit
streamlit run app/ui.py
```

---

## 📋 Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `SERPAPI_KEY` | Yes (for search) | Free at [serpapi.com](https://serpapi.com) (100 searches/month) |
| `BLOCKCHAIN_RPC_URL` | Yes | [Alchemy](https://alchemy.com) or [Infura](https://infura.io) Sepolia RPC |
| `BLOCKCHAIN_PRIVATE_KEY` | Yes | Testnet wallet — **never real funds** |
| `CONTRACT_ADDRESS` | Yes | Deploy contract first, then set this |
| `BLOCKCHAIN_CHAIN_ID` | No | Default: `11155111` (Sepolia) |
| `SEARCH_PROVIDER` | No | `serpapi` (default) or `demo` |
| `DEMO_MODE` | No | `true` to use labeled demo data without API keys |
| `IPFS_API_URL` | No | Pinata API URL for decentralized evidence storage |
| `BLOCK_EXPLORER_URL` | No | Etherscan URL for transaction links |

### Get Sepolia ETH
- [sepoliafaucet.com](https://sepoliafaucet.com)
- [faucets.chain.link/sepolia](https://faucets.chain.link/sepolia)

---

## 🧪 Testing

```bash
# Full test suite (100% mocked, no network/API keys needed)
pytest tests/ -v

# Run specific test class
pytest tests/test_pipeline.py::TestCanonicalization -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

**Test coverage includes:**
- RFC 8785 JSON canonicalization determinism
- SHA-256 fingerprinting + tamper detection
- Face engine (mocked InsightFace)
- Search provider factory and demo mode
- Blockchain client register/verify flow
- Full pipeline integration with all mocked subsystems

---

## 📦 Smart Contract

`contracts/ContentVerification.sol` (Solidity 0.8.24):
- **OpenZeppelin Ownable** access control
- `registerRecord(bytes32 fingerprint, bytes32 contentId, string sourceUrl)`
- `verifyRecord(bytes32 fingerprint) → bool`
- `getRecord(uint256 recordId) → full record tuple`
- `RecordRegistered` event for audit trail
- `fingerprintExists` mapping for O(1) verification
- `recordCount` and `getRecordIdByFingerprint` for lookup

**Deploy:**
```bash
# Local Hardhat
cd contracts && npx hardhat run scripts/deploy.js --network localhost

# Sepolia (requires funded wallet)
cd contracts && npx hardhat run scripts/deploy.js --network sepolia
```

**Verify on Etherscan:**
```bash
npx hardhat verify --network sepolia <CONTRACT_ADDRESS>
```

---

## 🎬 Demo Flow (for presentations)

1. `python scripts/make_demo_data.py` — generate test images
2. `python main.py demo/subject1.jpg` — run pipeline
3. Watch the 5 stages complete live:
   - `[1/5] FACE DETECTION` → ✓ face detected, hash computed
   - `[2/5] REVERSE IMAGE SEARCH` → ✓ result found
   - `[3/5] CONTENT PROOF` → ✓ SHA-256 fingerprint generated
   - `[4/5] BLOCKCHAIN REGISTRATION` → ✓ tx hash, block number
   - `[5/5] VERIFICATION` → ✓ VERIFIED
4. Click **"Simulate Tampering"** → fingerprint changes → **TAMPERED**

---

## 🛡️ Known Limitations

1. **Visual Similarity ≠ Identity**: Google Lens returns visually similar content, not proven identity matches. The pipeline always says "potential match."
2. **Search Rate Limits**: SerpApi free tier limits to 100 searches/month. Demo mode bypasses this with labeled data.
3. **Private Accounts**: Only publicly accessible social media can be searched. Private profiles require OAuth.
4. **Image Transformations**: Re-saving/re-encoding changes the fingerprint (by design for integrity).
5. **Blockchain Scope**: Proves data integrity and timestamp, NOT the truthfulness or licensing of content.
6. **Biometric Data**: Only SHA-256 hashes stored on-chain. Raw embeddings and images are never persisted on-chain.
7. **Local Chain vs Testnet**: Hardhat local chain is for testing only. Sepolia provides public verification.

---

## 📁 Project Structure

```
face-id-blockchain-verify/
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git exclusions
├── Dockerfile                 # Multi-stage container
├── docker-compose.yml         # Full-stack orchestration
├── app/
│   ├── __init__.py
│   ├── face.py               # InsightFace engine (buffalo_l)
│   ├── search.py             # SerpApi + demo providers
│   ├── hashing.py            # RFC 8785 canonical JSON + SHA-256
│   ├── blockchain.py         # Web3.py client (Sepolia/Hardhat)
│   ├── ipfs.py               # IPFS evidence storage
│   ├── pipeline.py           # Main pipeline orchestrator
│   └── ui.py                 # Streamlit dashboard
├── contracts/
│   ├── ContentVerification.sol   # Solidity smart contract
│   └── hardhat.config.js         # Hardhat configuration
├── scripts/
│   ├── deploy_contract.py    # Deploy to Sepolia/Hardhat
│   ├── make_demo_data.py     # Generate test images & data
│   └── record_demo.py        # Demo video generation
├── tests/
│   └── test_pipeline.py      # 100% mocked test suite
├── demo/                     # Generated demo images
├── artifacts/                # Pipeline output artifacts
├── deployments/              # Deployed contract info
└── docs/
    └── limitations.md        # Detailed limitations
```

---

## 🔧 Technologies

| Layer | Technology |
|-------|-----------|
| **Face Detection** | InsightFace `buffalo_l` (ArcFace, ResNet50, 512-D) |
| **Reverse Search** | SerpApi Google Lens (Image API → Lens query) |
| **Fingerprinting** | RFC 8785 canonical JSON → SHA-256 + Keccak-256 |
| **Blockchain** | Ethereum Sepolia testnet / local Hardhat |
| **Smart Contract** | Solidity 0.8.24 + OpenZeppelin Ownable |
| **Web3 Library** | web3.py |
| **Evidence Storage** | IPFS (Pinata) / data URI fallback |
| **Frontend** | Streamlit + Framer Motion |
| **Testing** | pytest (100% mocked) |
| **Container** | Docker multi-stage build |
| **Language** | Python 3.11+ |

---

## 📄 License

MIT

## ⚠️ Privacy & Ethics

- Use **only** consenting individuals' images or public demo data
- Reverse-image search results are for **public content** only
- **No biometric data is stored on-chain** — only SHA-256 hashes
- This is a **content provenance tool**, not a surveillance system
- Face recognition is **probabilistic** — a "potential match" is NOT proof of identity
- Never commit private keys, API keys, or personal data to source control
