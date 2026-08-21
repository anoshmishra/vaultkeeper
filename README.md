# VaultKeeper

<p align="center">
  <strong>Secure Local Vault for Passwords, Secrets, Notes & Files</strong><br>
  Privacy-first • Offline-first • macOS • Touch ID
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-macOS-black?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/security-encrypted-green?style=flat-square" alt="Security">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" alt="License">
</p>

<p align="center">
  A local-first encrypted vault for credentials, notes, files, TOTP secrets and other sensitive data.
</p>

---

## Overview

VaultKeeper is a macOS-focused security application designed to keep sensitive information inside a local encrypted vault.

It combines:

- Password-based authentication
- Argon2id password protection
- macOS Touch ID integration
- Encrypted credentials
- Secure notes
- Encrypted file storage
- Password generation and analysis
- TOTP management
- Backup management
- Session security
- Security and activity controls

VaultKeeper is designed around one principle:

> **Sensitive data should remain under the user's control.**

The application is designed for local and offline operation rather than relying on a remote service to store vault contents.

---

## Security Architecture

```mermaid
flowchart TD
    A[User] --> B{Authentication}

    B -->|Master Password| C[Key Derivation]
    B -->|Touch ID| D[macOS Authentication]

    C --> E[Vault Key]
    D --> E

    E --> F[Encrypted Vault]

    F --> G[Credentials]
    F --> H[Secure Notes]
    F --> I[Encrypted Files]
    F --> J[TOTP and Secrets]

    K[Session Security] --> F
    L[Encrypted Backups] --> F