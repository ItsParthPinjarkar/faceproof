import subprocess, time, os, sys, json
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

contracts_dir = r'C:\Users\parth\OneDrive\Documents\Default Project\face-id-blockchain-verify\contracts'
node_exe = r'C:\Program Files\nodejs\node.exe'

# Kill existing nodes
subprocess.run('taskkill /f /im node.exe', shell=True, capture_output=True)
time.sleep(1)

# Start Hardhat node using node.exe with hardhat's bin
# The .cmd file needs cmd.exe to run, so we use cmd /c
print("[1/4] Starting Hardhat node...")
proc = subprocess.Popen(
    ['cmd', '/c', 'npx', 'hardhat', 'node', '--hostname', '0.0.0.0', '--port', '8545'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=contracts_dir,
    text=True,
    bufsize=1
)
print(f"Node process PID: {proc.pid}")

# Wait for node
print("[2/4] Waiting for node...")
w3 = None
for i in range(20):
    try:
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        if w3.is_connected():
            break
    except:
        pass
    time.sleep(1)

if not w3 or not w3.is_connected():
    print("ERROR: Could not connect to Hardhat node")
    print("Trying to read node output...")
    # Try reading some output
    import select
    try:
        # Read available output
        import io
        remaining = proc.stdout.read(1000) if proc.stdout else ""
        print(f"Node output: {remaining[:500]}")
    except:
        pass
    proc.terminate()
    sys.exit(1)

print(f"Node connected. Chain ID: {w3.eth.chain_id}")
accounts = w3.eth.accounts
print(f"Accounts: {accounts}")

# Deploy contract using py-solc-x + web3.py
print("[3/4] Deploying contract with py-solc-x...")
from solcx import compile_source, install_solc
install_solc('0.8.24')

contract_file = Path(contracts_dir) / 'ContentVerification.sol'
with open(contract_file, 'r') as f:
    source_code = f.read()

compiled = compile_source(source_code, solc_version='0.8.24')
contract_name = 'ContentVerification'
interface = compiled[f'<stdin>:{contract_name}']

account = w3.eth.account.from_key(os.environ['BLOCKCHAIN_PRIVATE_KEY'])
w3.eth.default_account = account.address

contract = w3.eth.contract(abi=interface['abi'], bytecode=interface['bin'])
nonce = w3.eth.get_transaction_count(account.address)

tx = contract.constructor().build_transaction({
    'from': account.address,
    'nonce': nonce,
    'chainId': int(os.environ.get('BLOCKCHAIN_CHAIN_ID', '31337')),
    'gas': 3000000,
    'gasPrice': w3.to_wei('20', 'gwei'),
    'type': 2,
})

signed_tx = w3.eth.account.sign_transaction(tx, os.environ['BLOCKCHAIN_PRIVATE_KEY'])
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Deployment tx hash: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
contract_address = receipt['contractAddress']
print(f"Contract deployed at: {contract_address}")

# Save deployment info
deploy_dir = Path(__file__).parent.parent / 'deployments'
deploy_dir.mkdir(exist_ok=True)
deploy_info = {
    'contract_address': contract_address,
    'transaction_hash': tx_hash.hex(),
    'block_number': receipt['blockNumber'],
    'chain_id': 31337,
    'abi': interface['abi'],
    'network': 'local'
}
with open(deploy_dir / '31337.json', 'w') as f:
    json.dump(deploy_info, f, indent=2)

# Update .env
env_path = Path(__file__).parent.parent / '.env'
with open(env_path) as f:
    env_content = f.read()
env_content = env_content.replace(
    'CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3',
    f'CONTRACT_ADDRESS={contract_address}'
)
with open(env_path, 'w') as f:
    f.write(env_content)

print(f"\n[4/4] Setup complete! Contract at {contract_address}")
print("Node is still running in the background.")

# Keep node running
try:
    proc.wait()
except KeyboardInterrupt:
    proc.terminate()