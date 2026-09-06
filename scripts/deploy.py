import subprocess
import sys
import os

"""
Hardhat deployment script for ContentVerification.sol
"""
import subprocess
import json
import sys
import os
from pathlib import Path

# Ensure dependencies are installed
def install_deps():
    """Install Hardhat and dependencies."""
    contracts_dir = Path(__file__).parent.parent / 'contracts'
    os.chdir(contracts_dir)

    if not os.path.exists('package.json'):
        print("Initializing Hardhat project...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'py-solc-x'], check=True)
        subprocess.run(['npm', 'init', '-y'], check=True)
        subprocess.run(['npm', 'install', '@nomicfoundation/hardhat-toolbox', 'hardhat', '@openzeppelin/contracts'], check=True)
        subprocess.run(['npx', 'hardhat', 'init'], check=True)

    # Create hardhat.config.js
    config = """
require('@nomicfoundation/hardhat-toolbox');
require('dotenv').config();

module.exports = {
  solidity: {
    version: '0.8.24',
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    sepolia: {
      url: process.env.BLOCKCHAIN_RPC_URL,
      accounts: process.env.BLOCKCHAIN_PRIVATE_KEY ? [process.env.BLOCKCHAIN_PRIVATE_KEY] : undefined,
      chainId: 11155111,
      gasPrice: 20000000000
    },
    localhost: {
      url: 'http://127.0.0.1:8545',
      chainId: 31337
    }
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY
  }
};
"""
    with open('hardhat.config.js', 'w') as f:
        f.write(config)

def deploy_local():
    """Deploy to local Hardhat node."""
    os.chdir(Path(__file__).parent.parent / 'contracts')
    result = subprocess.run(
        ['npx', 'hardhat', 'run', 'scripts/deploy.js', '--network', 'localhost'],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

def deploy_sepolia():
    """Deploy to Ethereum Sepolia."""
    os.chdir(Path(__file__).parent.parent / 'contracts')
    result = subprocess.run(
        ['npx', 'hardhat', 'run', 'scripts/deploy.js', '--network', 'sepolia'],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

if __name__ == '__main__':
    network = os.environ.get('DEPLOY_NETWORK', 'local')
    if network == 'sepolia':
        deploy_sepolia()
    else:
        deploy_local()
