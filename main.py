#!/usr/bin/env python3
# main.py
"""
VaultKeeper - Advanced Secure Password Manager
============================================

A zero-knowledge encryption password manager with Touch ID support,
universal storage, and advanced security features for macOS.

Author: Anosh Mishra
Version: 1.0.0
"""

import sys
import os
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.main_window import VaultKeeperMainWindow
    from config.settings import settings
except ImportError as e:
    print(f"❌ Critical Error: Failed to import required modules")
    print(f"Error: {e}")
    print(f"Please ensure all VaultKeeper components are properly installed.")
    sys.exit(1)


def setup_logging():
    """Configure logging for VaultKeeper application"""
    
    # Create logs directory
    log_dir = Path.home() / '.vaultkeeper' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    log_file = log_dir / f'vaultkeeper_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create application logger
    logger = logging.getLogger('VaultKeeper')
    logger.info("=" * 60)
    logger.info("VaultKeeper Application Starting")
    logger.info(f"Version: 1.0.0")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info("=" * 60)
    
    return logger


def check_system_requirements():
    """
    Check system requirements and compatibility
    
    Returns:
        tuple: (success: bool, message: str)
    """
    
    # Check Python version (3.8+ required)
    if sys.version_info < (3, 8):
        return False, f"Python 3.8+ required. Current version: {sys.version}"
    
    # Check platform (macOS required for Touch ID)
    if sys.platform != 'darwin':
        return False, "VaultKeeper requires macOS for full functionality"
    
    # Check required directories exist
    required_dirs = ['ui', 'advanced', 'config']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        return False, f"Missing required directories: {', '.join(missing_dirs)}"
    
    # Check for critical files
    critical_files = [
        'ui/main_window.py',
        'advanced/encryption_advanced.py',
        'advanced/biometric_auth.py',
        'advanced/database_advanced.py'
    ]
    
    missing_files = []
    for file_path in critical_files:
        if not os.path.isfile(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing critical files: {', '.join(missing_files)}"
    
    return True, "All system requirements satisfied"


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for unhandled exceptions
    
    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
    """
    
    if issubclass(exc_type, KeyboardInterrupt):
        # Handle Ctrl+C gracefully
        print("\n🔒 VaultKeeper shutdown requested by user")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the exception
    logger = logging.getLogger('VaultKeeper')
    logger.critical("Unhandled exception occurred:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Show user-friendly error message
    print("\n" + "=" * 60)
    print("❌ VaultKeeper encountered an unexpected error")
    print("=" * 60)
    print(f"Error Type: {exc_type.__name__}")
    print(f"Error Message: {str(exc_value)}")
    print("\n📁 Error details have been logged to:")
    print(f"   ~/.vaultkeeper/logs/vaultkeeper_{datetime.now().strftime('%Y%m%d')}.log")
    print("\n🔧 Troubleshooting:")
    print("   1. Restart VaultKeeper")
    print("   2. Check system requirements")
    print("   3. Verify file permissions")
    print("   4. Review the log file for detailed error information")
    print("=" * 60)


def cleanup_on_exit():
    """Perform cleanup operations before application exit"""
    logger = logging.getLogger('VaultKeeper')
    logger.info("VaultKeeper application shutting down")
    
    # Clear any sensitive data from memory (if needed)
    # This is where you'd implement secure memory clearing
    
    logger.info("Cleanup completed")


def print_startup_banner():
    """Print VaultKeeper startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                    🔐 VaultKeeper v1.0.0                     ║
    ║            Advanced Secure Password Manager                  ║
    ║                                                              ║
    ║              Zero-Knowledge • Touch ID • Universal          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """
    Main entry point for VaultKeeper application
    
    This function handles application initialization, error checking,
    and graceful startup/shutdown procedures.
    """
    
    # Print startup banner
    print_startup_banner()
    
    # Setup logging
    try:
        logger = setup_logging()
    except Exception as e:
        print(f"⚠️  Warning: Could not setup logging: {e}")
        print("Application will continue without logging...")
        logger = None
    
    # Install global exception handler
    sys.excepthook = handle_exception
    
    # Check system requirements
    print("🔍 Checking system requirements...")
    requirements_ok, message = check_system_requirements()
    
    if not requirements_ok:
        print(f"❌ System Requirements Check Failed:")
        print(f"   {message}")
        print(f"\n💡 Please resolve the issues above and try again.")
        sys.exit(1)
    
    print("✅ System requirements satisfied")
    
    # Initialize and run application
    try:
        print("🚀 Initializing VaultKeeper...")
        
        # Create application instance
        app = VaultKeeperMainWindow()
        
        if logger:
            logger.info("VaultKeeper main window initialized successfully")
        
        print("✅ VaultKeeper initialized successfully")
        print("🔓 Starting secure session...\n")
        
        # Register cleanup function
        import atexit
        atexit.register(cleanup_on_exit)
        
        # Start the application
        app.run()
        
        if logger:
            logger.info("VaultKeeper application completed normally")
    
    except ImportError as e:
        error_msg = f"Failed to import required modules: {e}"
        print(f"❌ Import Error: {error_msg}")
        if logger:
            logger.error(error_msg)
        sys.exit(1)
    
    except FileNotFoundError as e:
        error_msg = f"Required file not found: {e}"
        print(f"❌ File Error: {error_msg}")
        if logger:
            logger.error(error_msg)
        sys.exit(1)
    
    except PermissionError as e:
        error_msg = f"Permission denied: {e}"
        print(f"❌ Permission Error: {error_msg}")
        print("💡 Try running with appropriate permissions or check file ownership")
        if logger:
            logger.error(error_msg)
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n🔒 VaultKeeper shutdown requested by user")
        if logger:
            logger.info("Application terminated by user (Ctrl+C)")
        sys.exit(0)
    
    except Exception as e:
        error_msg = f"Unexpected error during startup: {e}"
        print(f"❌ Startup Error: {error_msg}")
        print(f"🔍 Error Details: {traceback.format_exc()}")
        if logger:
            logger.critical(error_msg, exc_info=True)
        sys.exit(1)


def version_info():
    """Display version information"""
    print("VaultKeeper v1.0.0")
    print("Advanced Secure Password Manager for macOS")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")


def help_info():
    """Display help information"""
    help_text = """
VaultKeeper - Advanced Secure Password Manager

Usage:
    python main.py              Start VaultKeeper GUI
    python main.py --version    Show version information
    python main.py --help       Show this help message

Features:
    • Zero-knowledge encryption with AES-256
    • Touch ID biometric authentication
    • Universal secure file storage
    • Advanced password generation
    • Comprehensive audit logging
    • Cross-platform compatibility

For more information, visit: https://github.com/yourusername/vaultkeeper
    """
    print(help_text)


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--version', '-v']:
            version_info()
            sys.exit(0)
        elif arg in ['--help', '-h']:
            help_info()
            sys.exit(0)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    
    # Run the main application
    main()
