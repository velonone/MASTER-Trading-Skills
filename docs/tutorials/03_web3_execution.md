# Tutorial 3: Web3 Execution

Execute trades on Ethereum DEXs with MEV protection.

## Setup

```python
from skills.execution.web3 import Web3DEXExecutor

executor = Web3DEXExecutor(
    rpc_url="https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY",
    private_key="0xYOUR_PRIVATE_KEY",
    mev_protection="flashbots",  # default
)
```

**Security Note**: Never hardcode private keys. Use environment variables:

```python
import os
executor = Web3DEXExecutor(
    rpc_url=os.getenv("ETH_RPC_URL"),
    private_key=os.getenv("PRIVATE_KEY"),
)
```

## Checking Gas Prices

```python
gas = await executor.get_gas_price()
print(f"Base Fee: {gas['base_fee_per_gas']} wei")
print(f"Max Priority: {gas['max_priority_fee_per_gas']} wei")
print(f"Max Fee: {gas['max_fee_per_gas']} wei")
```

## Executing a Swap

```python
from decimal import Decimal

tx_hash = await executor.swap_exact_in(
    token_in="0xA0b86a33E6441e6C7D3D4B4f6c7E8F9a0B1c2D3e",  # Example token
    token_out="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
    amount_in=Decimal("1.5"),
    min_amount_out=Decimal("1.4"),
    deadline_seconds=300,
)

print(f"Transaction submitted: {tx_hash}")
```

## Confirming a Transaction

```python
receipt = await executor.await_confirmation(tx_hash, confirmations=2)

if receipt["status"] == "success":
    print(f"Confirmed in block {receipt['block_number']}")
    print(f"Gas used: {receipt['gas_used']}")
else:
    print("Transaction failed!")
```

## MEV Protection Options

| Provider | Best For | Trade-off |
|----------|----------|-----------|
| `flashbots` | General use | Slightly slower inclusion |
| `flashbots_standard` | Maximum privacy | Slowest |
| `mevblocker` | Fast inclusion | Less privacy than Flashbots |
| `eden` | Eden Network users | Ecosystem specific |

## Testing on Goerli

Before mainnet, test on Goerli:

```python
executor = Web3DEXExecutor(
    rpc_url="https://eth-goerli.g.alchemy.com/v2/YOUR_API_KEY",
    private_key="0x...",
    mev_protection=None,  # Testnets don't need MEV protection
    chain_id=5,
)
```
