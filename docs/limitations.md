# Known Limitations

## Reverse Image Search Accuracy
- Google Lens returns **visual similarity** matches, not identity verification
- Testing consistently showed demographically-similar strangers rather than the actual person
- A purpose-built face-recognition search API (PimEyes, FaceCheck.ID) would be needed for genuine identity matching but requires paid credits
- SerpApi free tier limits to 100 searches/month

## Image Upload Requirement
- SerpApi requires a URL, not raw file upload
- The pipeline uploads the cropped face to a temporary host (or uses demo mode)
- Uploads are temporary but mean the photo briefly leaves the machine
- Some hosts may not be reliably crawled by Google Lens

## Biometric Privacy
- Only SHA-256 hashes stored on-chain, never raw embeddings
- No face images, embeddings, or personal data stored on blockchain
- Writing raw biometric data to an immutable public ledger would be irresponsible

## Technical Limitations
- **Single-face assumption**: Only the largest face is encoded; group photos need modification
- **First-run model download**: InsightFace downloads ~326MB buffalo_l weights on first execution
- **Gas constraints**: Sepolia testnet gas is free but faucets can be rate-limited
- **Contract deployment**: The smart contract must be deployed separately before use
- **IPFS optional**: If IPFS is not configured, evidence is stored as data URIs (less decentralized)
- **Local vs Testnet**: Hardhat local chain provides no real security guarantees

## Ethical Scope
- Use only consenting individuals' images or public demo data
- Reverse-image search results are for publicly accessible content only
- This is a **content provenance tool**, not a surveillance system
- Face recognition is **probabilistic** — a "potential match" is NOT proof of identity
- Never commit private keys, API keys, or personal data to source control

## Blockchain Scope
- Blockchain proves the **integrity** of recorded data, not its **truthfulness** or licensing
- Confirmed on-chain records cannot be mutated
- Local testnet transactions are not production-grade legal evidence
