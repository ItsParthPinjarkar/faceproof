# FaceProof — Deployment Guide

## Deploy to Ethereum Sepolia

### Prerequisites

- Python 3.11+
- Node.js 18+
- Sepolia ETH (from a faucet)
- Alchemy or Infura RPC URL
- MetaMask wallet

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
npm install -g hardhat
```

### Step 2: Compile Contract

```bash
cd contracts
npm install @nomicfoundation/hardhat-toolbox @openzeppelin/contracts hardhat
npx hardhat compile
```

### Step 3: Deploy to Sepolia

```bash
# Method 1: Using the deploy script
python scripts/deploy_contract.py

# Method 2: Using Hardhat directly
npx hardhat run scripts/deploy.js --network sepolia
```

### Step 4: Verify on Etherscan

```bash
npx hardhat verify --network sepolia <CONTRACT_ADDRESS>
```

### Step 5: Configure Environment

```bash
cp .env.example .env
# Fill in:
# BLOCKCHAIN_RPC_URL=your_alchemy_sepolia_url
# BLOCKCHAIN_PRIVATE_KEY=your_wallet_private_key
# CONTRACT_ADDRESS=<deployed_address>
# BLOCKCHAIN_CHAIN_ID=11155111
```

### Step 6: Run the Pipeline

```bash
python main.py path/to/face.jpg
# Or in demo mode:
DEMO_MODE=true python main.py demo/subject1.jpg
```

## Deploy to Local Hardhat (Testing)

```bash
# Terminal 1: Start local node
npx hardhat node

# Terminal 2: Deploy contract
npx hardhat run scripts/deploy.js --network localhost

# Terminal 3: Run pipeline
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545 \
BLOCKCHAIN_PRIVATE_KEY=0xac0974bec39a17e36ba4a4b3d55a5d3f... \
CONTRACT_ADDRESS=<deployed_address> \
DEMO_MODE=true \
python main.py demo/subject1.jpg
```

## Deploy to Docker

```bash
# Build and start everything
docker compose up --build

# Deploy contract (separate command)
docker compose --profile deploy run deployer
```

## IPFS Configuration (Optional)

Get a free Pinata API key at [pinata.cloud](https://pinata.cloud). Then add to `.env`:

```
IPFS_API_URL=https://api.pinata.cloud
IPFS_PINNING_KEY=your_pinata_key
```

Evidence will be pinned to IPFS instead of stored as data URIs.
