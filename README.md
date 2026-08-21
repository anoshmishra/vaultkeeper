# vaultkeeper







VaultKeeper is a modern, zero-knowledge encrypted password manager designed for macOS. It integrates Touch ID, supports universal encrypted storage (credentials, files, notes), and provides a professional dark-themed UI.

VaultKeeper ensures military-grade encryption, biometric authentication, and zero data leakage, making it ideal for both personal security and enterprise-grade protection.

✨ Key Features
🔒 Advanced Security

Zero-Knowledge Design – Data is encrypted locally; developers cannot access your secrets.

AES-256 Encryption – Robust, industry-standard symmetric encryption.

Argon2id Password Hashing – Memory-hard password hashing algorithm.

PBKDF2 Key Derivation – With 100,000+ iterations.

Secure Memory Handling – Clears sensitive data after use.

👆 Biometric Authentication

Touch ID Integration – Faster, hardware-level security.

macOS Secure Enclave support.

Master Password Fallback in case biometrics fail.

Auto-lock & session management after inactivity.

📦 Universal Storage

Store documents, images, and videos (up to 100MB each).

Encrypted text notes with full-text search.

Organize with categories and tags.

🔑 Password Management

Customizable password generator with length, charset, symbols.

Strength analysis with real-time feedback.

Presets: PIN, passphrase, high-security, web-safe.

Exclude ambiguous characters for usability.

🎨 User Interface

Dark theme for eye comfort.

Clean navigation with categorized views.

Smart search & filtering.

Favorites system for frequently used items.

📊 Auditing & Analytics

Activity logs of operations.

Usage statistics & password strength metrics.

Breach detection (check for compromised credentials).

Automated backups with retention policies.

⚡ Quick Start
Prerequisites

macOS 10.15+ (Touch ID support requires Apple Silicon).

Python 3.8+

Xcode Command Line Tools

2GB RAM, 100MB free space

Installation
git clone https://github.com/anoshmishra/vaultkeeper.git
cd vaultkeeper

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python3 main.py

First-Time Setup

Launch: python3 main.py

Create a master password (cannot be recovered).

Optionally enable Touch ID.

Configure:

Auto-lock timeout (default: 15 min).

Clipboard auto-clear (default: 30s).

Backup location & retention.

🛠 Project Architecture
vaultkeeper/
│── main.py                  # Application entry point
│── README.md                # Documentation
│── requirements.txt         # Dependencies
│── LICENSE                  # MIT License
│
├── config/                  # Settings & preferences
├── ui/                      # User interface (main window, generator, settings)
├── advanced/                # Core modules: encryption, biometrics, DB, storage
├── tests/                   # Unit and security test suite
└── tools/                   # Utilities: debug, migration, schema fix, recovery

📖 Usage Guide
Launch Options
python3 main.py          # Standard launch
python3 main.py --debug  # With logging
python3 main.py --version

Credentials

Add Password → Site, username, password.

Edit → Modify existing credentials.

Copy → Clipboard clears after 30s.

Favorites → Mark with ⭐.

Storage

Upload Files – encrypted in vault.

Add Notes – encrypted with full-text search.

Organize – by tags, categories, and type.

Search & Organization

Real-time search bar.

Filter by type (notes, files, credentials).

Sort by name, date, usage.

🔧 Troubleshooting
Common Issues

Invalid Master Password

Check spelling.

Run tools/test_auth.py.

Run tools/debug_vault_data.py.

Database Schema Errors

python3 tools/fix_database_schema.py


Touch ID Not Working

macOS 10.15+, enrolled fingerprints.

Run:

python3 -c "from advanced.biometric_auth import BiometricAuth; BiometricAuth().debug_touchid_setup()"


App Won’t Start

python3 --version
source venv/bin/activate
pip install -r requirements.txt
python3 -v main.py

🔐 Security Architecture
Encryption Flow

User enters master password.

Master key derived via PBKDF2 + salt.

Vault key (stored encrypted) unlocked.

Vault key decrypts data.

(Optional) Touch ID decrypts stored key in macOS Keychain.

Data Protection

AES-256 Fernet authenticated encryption.

Unique IV & salt per operation.

Argon2id hashing for passwords.

Session keys cleared from memory.

Zero-knowledge – no recovery without master password.

👩‍💻 Development
Dev Setup
pip install -r requirements-dev.txt
pre-commit install

Tests
pytest tests/ -v
pytest --cov=advanced --cov-report=html

Code Quality
flake8 advanced/ ui/ tests/
pylint advanced/ ui/
mypy advanced/ ui/
bandit -r advanced/ ui/

⚠ Security Notes

Master Password cannot be recovered – backup required.

Backups must be tested regularly.

VaultKeeper runs offline only – no telemetry, no servers.

Keep macOS + FileVault updated for full security.

📜 License

MIT License © 2024–2025 Anosh Mishra

🙌 Acknowledgments

Lead Developer: Anosh Mishra

Community contributors: Testing, feedback

Special thanks: Python Cryptography, macOS Security, OWASP

📬 Support

GitHub Issues – Bug reports & features.

Email – Security vulnerabilities.

General support – anoshmishra09@gmail.com

🧾 Important Takeaways

VaultKeeper is offline-only (highest privacy).

Master password is critical → no recovery if lost.

Touch ID + Secure Enclave provide hardware-level security.

Universal encrypted storage → passwords, files, notes.

Automated backups are essential for disaster recovery.
