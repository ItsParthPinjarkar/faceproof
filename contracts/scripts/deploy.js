import { ethers } from 'hardhat';

async function main() {
  const ContentVerification = await ethers.getContractFactory('ContentVerification');
  const contentVerification = await ContentVerification.deploy();
  await contentVerification.waitForDeployment();

  const address = await contentVerification.getAddress();
  console.log('ContentVerification deployed to:', address);

  const tx = contentVerification.deploymentTransaction();
  console.log('Transaction hash:', tx.hash);
  console.log('Block number:', tx.blockNumber);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});