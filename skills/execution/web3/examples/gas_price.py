"""
Example: EIP-1559 Gas Price Fetch
==================================
Run: python -m skills.execution.web3.examples.gas_price
"""
import asyncio
from skills.execution.web3 import Web3DEXExecutor


async def main():
    executor = Web3DEXExecutor(rpc_url="https://eth.llamarpc.com")
    try:
        gas = await executor.get_gas_price()
        print(f"base_fee_per_gas: {gas['base_fee_per_gas']}")
        print(f"max_priority_fee_per_gas: {gas['max_priority_fee_per_gas']}")
        print(f"max_fee_per_gas: {gas['max_fee_per_gas']}")
    except Exception as exc:
        print(f"RPC error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
