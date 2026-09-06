"""
Hardhat deployment script for ContentVerification.sol.
Run with: python scripts/deploy_contract.py
"""
import os
import sys
import json
import subprocess
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Ensure py-solc-x is available
try:
    from solcx import compile_source, install_solc
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'py-solc-x'], check=True)
    from solcx import compile_source, install_solc

def deploy():
    """Deploy the ContentVerification contract."""
    contracts_dir = Path(__file__).parent.parent / 'contracts'
    contract_file = contracts_dir / 'ContentVerification.sol'

    # Install solidity compiler
    install_solc('0.8.24')

    # Compile
    with open(contract_file, 'r') as f:
        source_code = f.read()

    compiled = compile_source(source_code, solc_version='0.8.24')

    # Find the contract interface
    contract_name = 'ContentVerification'
    interface = compiled[f'<stdin>:{contract_name}']

    # Get network config
    rpc_url = os.environ['BLOCKCHAIN_RPC_URL']
    private_key = os.environ['BLOCKCHAIN_PRIVATE_KEY']
    chain_id = int(os.environ.get('BLOCKCHAIN_CHAIN_ID', '11155111'))

    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to {rpc_url}")

    account = w3.eth.account.from_key(private_key)
    w3.eth.default_account = account.address

    # Deploy
    contract = w3.eth.contract(abi=interface['abi'], bytecode=interface['bin'])

    nonce = w3.eth.get_transaction_count(account.address)

    tx = contract.constructor().build_transaction({
        'from': account.address,
        'nonce': nonce,
        'chainId': chain_id,
        'gas': 3000000,
        'maxFeePerGas': w3.to_wei('20', 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei('1', 'gwei'),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Deployment tx hash: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    contract_address = receipt['contractAddress']

    print(f"\n✅ Contract deployed at: {contract_address}")
    print(f"   Block: {receipt['blockNumber']}")
    print(f"   Gas used: {receipt['gasUsed']}")
    print(f"   Chain ID: {chain_id}")

    # Save deployment info
    deploy_info = {
        'contract_address': contract_address,
        'transaction_hash': tx_hash.hex(),
        'block_number': receipt['blockNumber'],
        'chain_id': chain_id,
        'abi': interface['abi'],
        'network': 'sepolia' if chain_id == 11155111 else 'local'
    }

    deploy_dir = Path(__file__).parent.parent / 'deployments'
    deploy_dir.mkdir(exist_ok=True)
    deploy_file = deploy_dir / f"{chain_id}.json"
    with open(deploy_file, 'w') as f:
        json.dump(deploy_info, f, indent=2, default=str)

    # Write contract address to .env or print for manual copy
    print(f"\nSet CONTRACT_ADDRESS={contract_address} in your .env file")

    # Verify on Etherscan if API key available
    if os.environ.get('ETHERSCAN_API_KEY'):
        print("\nVerifying on Etherscan...")
        try:
            subprocess.run(
                ['npx', 'hardhat', 'verify', '--network', 'sepolia', contract_address],
                check=True
            )
        except:
            print("Auto-verification skipped (use Remix or Hardhat CLI)")

if __name__ == '__main__':
    deploy()
