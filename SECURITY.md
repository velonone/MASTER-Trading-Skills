# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.0.x   | Yes |
| < 3.0   | No                |

## Reporting a Vulnerability

If you discover a security vulnerability in MASTER Trading, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainers at `security@velonlabs.io` with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if available)

You will receive a response within 48 hours acknowledging receipt. We aim to resolve critical vulnerabilities within 7 days.

## Security Considerations

### Private Keys
- Never commit private keys to the repository
- Use environment variables or secure key management (AWS KMS, HashiCorp Vault)
- The `Web3DEXExecutor` accepts private keys but recommends KMS integration for production

### API Keys
- Store exchange API keys in `.env` files (never committed)
- Use minimum required permissions on exchange API keys
- Rotate keys regularly

### Smart Contract Interactions
- All DEX interactions should be tested on testnets before mainnet
- Use Slither static analysis for any generated Solidity code
- Enable formal verification (Halmos / Certora) for critical paths

### MEV Protection
- MEV protection is enabled by default for all Web3 transactions
- Flashbots Protect RPC is the recommended default for Ethereum mainnet

## Audit Status

This project has not undergone a formal third-party security audit. Use at your own risk for production trading.
