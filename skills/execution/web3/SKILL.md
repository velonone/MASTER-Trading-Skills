---
name: execution_web3
version: "2.0.0"
description: Web3 DEX execution layer — MEV protection, gas optimization, on-chain swaps
author: VelonLabs
skills:
  - name: web3_dex_executor
    class: Web3DEXExecutor
    module: skills.execution.web3.dex_executor
    description: Async on-chain DEX execution with MEV protection
    triggers: [swap, dex, web3, execution]
  - name: mev_protection
    class: MEVProtection
    module: skills.execution.web3.mev_protection
    description: MEV-protected RPC endpoint selector
    triggers: [mev, rpc, protection]
dependencies:
  - web3>=7.0
  - eth-account>=0.10
---

# Web3 Execution Layer

## Web3DEXExecutor

Unified execution seam for DEX connectivity. Implements `BaseConnector`.

```python
from skills.execution.web3 import Web3DEXExecutor

executor = Web3DEXExecutor(
    rpc_url="https://eth.llamarpc.com",
    mev_protection="flashbots",
)

# Unified connector interface
report = await executor.place_order(order)
pos = await executor.fetch_position("ETH/USDT")

# Agent dispatch
result = await executor.run({
    "action": "swap",
    "token_in": "0x...",
    "token_out": "0x...",
    "amount_in": "1.5",
})
```

## MEVProtection

Select MEV-protected RPC endpoints (Flashbots, MEV Blocker, Eden).
