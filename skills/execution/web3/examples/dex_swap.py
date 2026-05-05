"""
Example: DEX Swap via Web3DEXExecutor
======================================
Run: python -m skills.execution.web3.examples.dex_swap
"""

import asyncio

from skills.execution.web3 import Web3DEXExecutor


async def main():
    executor = Web3DEXExecutor(
        rpc_url="https://eth.llamarpc.com",
        mev_protection="flashbots",
    )

    # Agent dispatch interface
    tx_hash = await executor.run(
        {
            "action": "swap",
            "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "token_out": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
            "amount_in": "1.0",
            "min_amount_out": "1800.0",
        }
    )
    print(f"Swap tx_hash: {tx_hash}")

    # Gas price inquiry
    gas = await executor.run({"action": "gas"})
    print(f"Base fee: {gas.get('base_fee_per_gas')}")


if __name__ == "__main__":
    asyncio.run(main())
