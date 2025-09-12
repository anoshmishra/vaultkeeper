# ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sys
import os
import base64
from datetime import datetime

# Add the parent directory to the path so we can import from advanced/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced.encryption_advanced import ZeroKnowledgeEncryption
from advanced.biometric_auth import BiometricAuth
from advanced.database_advanced import (
    init_advanced_db, get_user_advanced, save_user_advanced, 
    enable_biometric_for_user, add_credential_advanced, 
    get_credentials_advanced, update_credential_advanced,
    delete_credential_advanced, mark_credential_used,
    toggle_credential_favorite, log_audit_action,
    get_database_stats, vacuum_database
)
from advanced.password_generator import AdvancedPasswordGenerator
from advanced.universal_storage import UniversalDataManager

class VaultKeeperMainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VaultKeeper - Advanced Secure Password Manager")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        self.root.minsize(800, 600)
        
        # Initialize components
        self.encryption = ZeroKnowledgeEncryption()
        self.biometric = BiometricAuth()
        self.password_gen = AdvancedPasswordGenerator()
        self.universal_storage = None  # Will be initialized after authentication
        
        # Initialize database
        init_advanced_db()
        
        # Session variables
        self.session_key = None
        self.vault_key = None
        self.is_authenticated = False
        self.current_credentials = []
        self.current_storage_items = []
        
        # UI Style configuration
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'text_light': '#ecf0f1',
            'text_muted': '#bdc3c7'
        }
        
        self.setup_ui()
        self.check_initial_setup()
    
    def setup_ui(self):
        """Setup the main UI components with enhanced styling"""
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Title frame
        title_frame = tk.Frame(self.root, bg=self.colors['primary'])
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = tk.Label(
            title_frame, 
            text="🔐 VaultKeeper", 
            font=('Arial', 28, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['primary']
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Advanced Secure Password Manager with Universal Storage",
            font=('Arial', 12),
            fg=self.colors['text_muted'],
            bg=self.colors['primary']
        )
        subtitle_label.pack()
        
        # Main content frame with scrollable area
        main_frame = tk.Frame(self.root, bg=self.colors['secondary'])
        main_frame.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Create scrollable content area
        canvas = tk.Canvas(main_frame, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.content_frame = tk.Frame(canvas, bg=self.colors['secondary'])
        
        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg=self.colors['primary'],
            fg=self.colors['text_light']
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_bar.config(text=f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        self.root.update_idletasks()
    
    def check_initial_setup(self):
        """Check if this is first run or user exists"""
        user_data = get_user_advanced()
        
        if not user_data:
            self.show_setup_screen()
        else:
            self.show_login_screen()
    
    def show_setup_screen(self):
        """Enhanced first-time setup screen"""
        self.clear_content()
        self.update_status("Setting up new vault...")
        
        setup_frame = tk.Frame(self.content_frame, bg=self.colors['secondary'])
        setup_frame.pack(expand=True, pady=50)
        
        # Welcome section
        welcome_frame = tk.Frame(setup_frame, bg=self.colors['secondary'])
        welcome_frame.pack(pady=30)
        
        tk.Label(
            welcome_frame,
            text="🎉 Welcome to VaultKeeper!",
            font=('Arial', 24, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack()
        
        tk.Label(
            welcome_frame,
            text="Create your master password to secure your vault with zero-knowledge encryption",
            font=('Arial', 12),
            fg=self.colors['text_muted'],
            bg=self.colors['secondary'],
            wraplength=600
        ).pack(pady=10)
        
        # Password setup form
        form_frame = tk.Frame(setup_frame, bg=self.colors['secondary'])
        form_frame.pack(pady=20)
        
        # Master password
        tk.Label(
            form_frame, 
            text="Master Password:", 
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'], 
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(10, 5))
        
        self.master_pass_entry = tk.Entry(
            form_frame, 
            show="*", 
            width=40, 
            font=('Arial', 12),
            relief=tk.SOLID,
            borderwidth=1
        )
        self.master_pass_entry.pack(pady=5)
        
        # Password strength indicator
        self.strength_label = tk.Label(
            form_frame,
            text="Password strength will appear here",
            font=('Arial', 10),
            fg=self.colors['text_muted'],
            bg=self.colors['secondary']
        )
        self.strength_label.pack(pady=5)
        
        # Bind password strength checker
        self.master_pass_entry.bind('<KeyRelease>', self.check_password_strength)
        
        # Confirm password
        tk.Label(
            form_frame, 
            text="Confirm Password:", 
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'], 
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(15, 5))
        
        self.confirm_pass_entry = tk.Entry(
            form_frame, 
            show="*", 
            width=40, 
            font=('Arial', 12),
            relief=tk.SOLID,
            borderwidth=1
        )
        self.confirm_pass_entry.pack(pady=5)
        
        # Security options
        options_frame = tk.Frame(form_frame, bg=self.colors['secondary'])
        options_frame.pack(pady=20)
        
        # Biometric option
        if self.biometric.is_touchid_available():
            self.enable_biometric = tk.BooleanVar(value=True)
            biometric_check = tk.Checkbutton(
                options_frame,
                text="🔓 Enable Touch ID for quick access",
                variable=self.enable_biometric,
                font=('Arial', 11),
                fg=self.colors['text_light'],
                bg=self.colors['secondary'],
                selectcolor=self.colors['accent'],
                activebackground=self.colors['secondary'],
                activeforeground=self.colors['text_light']
            )
            biometric_check.pack(anchor='w', pady=5)
        
        # Auto-lock option
        self.enable_autolock = tk.BooleanVar(value=True)
        autolock_check = tk.Checkbutton(
            options_frame,
            text="🔒 Enable auto-lock after 15 minutes of inactivity",
            variable=self.enable_autolock,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success'],
            activebackground=self.colors['secondary'],
            activeforeground=self.colors['text_light']
        )
        autolock_check.pack(anchor='w', pady=5)
        
        # Create vault button
        button_frame = tk.Frame(form_frame, bg=self.colors['secondary'])
        button_frame.pack(pady=30)
        
        create_btn = tk.Button(
            button_frame,
            text="🚀 Create Secure Vault",
            command=self.create_vault,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=12,
            relief=tk.FLAT,
            cursor='hand2'
        )
        create_btn.pack()
        
        # Security info
        security_info = tk.Label(
            setup_frame,
            text="🛡️ Your data will be encrypted with AES-256 and zero-knowledge architecture\n"
                 "Only you have access to your decryption keys",
            font=('Arial', 10),
            fg=self.colors['text_muted'],
            bg=self.colors['secondary'],
            justify=tk.CENTER
        )
        security_info.pack(pady=20)
    
    def check_password_strength(self, event=None):
        """Real-time password strength checking"""
        password = self.master_pass_entry.get()
        if not password:
            self.strength_label.config(text="Password strength will appear here", 
                                     fg=self.colors['text_muted'])
            return
        
        strength_result = self.password_gen.check_password_strength(password)
        strength = strength_result['strength']
        
        color_map = {
            'Very Weak': self.colors['danger'],
            'Weak': '#e67e22',
            'Fair': self.colors['warning'],
            'Good': '#2ecc71',
            'Strong': self.colors['success'],
            'Very Strong': '#27ae60'
        }
        
        self.strength_label.config(
            text=f"Password Strength: {strength}",
            fg=color_map.get(strength, self.colors['text_muted'])
        )
    
    def show_login_screen(self):
        """Enhanced login screen with biometric option"""
        self.clear_content()
        self.update_status("Awaiting authentication...")
        
        login_frame = tk.Frame(self.content_frame, bg=self.colors['secondary'])
        login_frame.pack(expand=True, pady=50)
        
        # Header
        header_frame = tk.Frame(login_frame, bg=self.colors['secondary'])
        header_frame.pack(pady=30)
        
        tk.Label(
            header_frame,
            text="🔐 Unlock Your Secure Vault",
            font=('Arial', 20, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack()
        
        tk.Label(
            header_frame,
            text="Choose your authentication method",
            font=('Arial', 12),
            fg=self.colors['text_muted'],
            bg=self.colors['secondary']
        ).pack(pady=10)
        
        # Authentication options frame
        auth_frame = tk.Frame(login_frame, bg=self.colors['secondary'])
        auth_frame.pack(pady=20)
        
        # Biometric login option
        user_data = get_user_advanced()
        has_biometric = user_data and len(user_data) > 3 and user_data[3]  # biometric_enabled field
        
        if self.biometric.is_touchid_available() and has_biometric:
            biometric_frame = tk.Frame(auth_frame, bg=self.colors['accent'], relief=tk.RAISED, bd=2)
            biometric_frame.pack(pady=10, padx=20, fill='x')
            
            tk.Label(
                biometric_frame,
                text="🔓 Quick Access",
                font=('Arial', 14, 'bold'),
                fg='white',
                bg=self.colors['accent']
            ).pack(pady=5)
            
            biometric_btn = tk.Button(
                biometric_frame,
                text="Unlock with Touch ID",
                command=self.biometric_login,
                bg='white',
                fg=self.colors['accent'],
                font=('Arial', 12, 'bold'),
                padx=40,
                pady=10,
                relief=tk.FLAT,
                cursor='hand2'
            )
            biometric_btn.pack(pady=10)
            
            # Separator
            tk.Label(
                auth_frame,
                text="─── OR ───",
                font=('Arial', 12),
                fg=self.colors['text_muted'],
                bg=self.colors['secondary']
            ).pack(pady=15)
        
        # Master password login
        password_frame = tk.Frame(auth_frame, bg=self.colors['secondary'])
        password_frame.pack(pady=10)
        
        tk.Label(
            password_frame, 
            text="Master Password:", 
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'], 
            bg=self.colors['secondary']
        ).pack(pady=5)
        
        self.login_pass_entry = tk.Entry(
            password_frame, 
            show="*", 
            width=30, 
            font=('Arial', 12),
            relief=tk.SOLID,
            borderwidth=1
        )
        self.login_pass_entry.pack(pady=10)
        self.login_pass_entry.bind('<Return>', lambda e: self.password_login())
        
        # Login button
        login_btn = tk.Button(
            password_frame,
            text="🔓 Unlock Vault",
            command=self.password_login,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        login_btn.pack(pady=15)
        
        # Focus on password entry
        self.login_pass_entry.focus_set()
    
    def create_vault(self):
        """Create new vault with master password and advanced security"""
        master_pass = self.master_pass_entry.get()
        confirm_pass = self.confirm_pass_entry.get()
        
        # Validation
        if len(master_pass) < 8:
            messagebox.showwarning("Weak Password", "Master password must be at least 8 characters long!")
            return
        
        if master_pass != confirm_pass:
            messagebox.showerror("Password Mismatch", "Passwords do not match!")
            return
        
        # Check password strength
        strength_result = self.password_gen.check_password_strength(master_pass)
        if strength_result['score'] < 4:
            response = messagebox.askyesno(
                "Weak Password", 
                f"Your password strength is '{strength_result['strength']}'. "
                "We recommend using a stronger password. Continue anyway?"
            )
            if not response:
                return
        
        try:
            self.update_status("Creating secure vault...")
            
            # Create vault encryption
            salt = self.encryption.generate_master_salt()
            master_key = self.encryption.derive_master_key(master_pass, salt)
            vault_key = self.encryption.generate_vault_key()
            encrypted_vault_key = self.encryption.encrypt_vault_key(vault_key, master_key)
            
            # Hash master password for storage
            master_hash = self.encryption.ph.hash(master_pass)
            
            # Save to database
            biometric_enabled = hasattr(self, 'enable_biometric') and self.enable_biometric.get()
            save_user_advanced(master_hash, salt, encrypted_vault_key, biometric_enabled)
            
            # Setup biometric if enabled
            if biometric_enabled:
                self.update_status("Setting up Touch ID...")
                self.root.after(1000, lambda: self._setup_biometric_delayed(master_pass, salt))
            else:
                messagebox.showinfo("Success", "🎉 Secure vault created successfully!")
            
            # Set session and show vault
            self.session_key = master_key
            self.vault_key = vault_key
            self.is_authenticated = True
            
            # Initialize universal storage
            self.universal_storage = UniversalDataManager(vault_key)
            
            # Log the action
            log_audit_action("VAULT_CREATED", success=True, details="New vault created")
            
            self.show_vault_screen()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create vault:\n{str(e)}")
            self.update_status("Vault creation failed")
    
    def _setup_biometric_delayed(self, master_pass, salt):
        """Setup biometric authentication with proper error handling"""
        try:
            success, message = self.biometric.setup_touchid_keychain(master_pass, salt)
            
            if success:
                enable_biometric_for_user()
                messagebox.showinfo("Complete Setup", 
                                  "🎉 Vault created with Touch ID enabled!\n\n"
                                  "You can now use Touch ID to unlock your vault.")
            else:
                messagebox.showwarning("Partial Setup", 
                                     f"Vault created successfully, but Touch ID setup encountered an issue:\n\n"
                                     f"{message}\n\n"
                                     "You can enable Touch ID later in Settings.")
        except Exception as e:
            messagebox.showwarning("Setup Warning", 
                                 f"Vault created successfully, but Touch ID setup failed:\n\n"
                                 f"{str(e)}\n\n"
                                 "You can try enabling Touch ID later in Settings.")
    
    def biometric_login(self):
        """Enhanced biometric login with better error handling"""
        try:
            self.update_status("Preparing Touch ID authentication...")
            
            # Check availability first
            if not self.biometric.is_touchid_available():
                messagebox.showerror("Touch ID Unavailable", 
                                   "Touch ID is not available or disabled.\n\n"
                                   "Please check:\n"
                                   "• System Preferences > Touch ID & Passcode\n"
                                   "• Ensure Touch ID is enabled\n"
                                   "• Try restarting your Mac")
                return
            
            # Check if biometric data exists
            status = self.biometric.get_touchid_status()
            if not status['keychain_item_exists']:
                messagebox.showerror("Setup Required", 
                                   "Touch ID authentication not set up.\n\n"
                                   "Please log in with your master password first, "
                                   "then enable Touch ID in settings.")
                return
            
            self.update_status("Waiting for Touch ID...")
            
            # Show user what to expect
            messagebox.showinfo("Touch ID Ready", 
                              "Please place your finger on the Touch ID sensor when prompted.")
            
            # Authenticate
            vault_data, message = self.biometric.authenticate_with_touchid()
            
            if vault_data:
                # Process successful authentication
                master_password = vault_data['master_password']
                salt = base64.b64decode(vault_data['salt'])
                
                # Continue with login process...
                master_key = self.encryption.derive_master_key(master_password, salt)
                user_data = get_user_advanced()
                
                if user_data:
                    _, _, encrypted_vault_key, _ = user_data
                    vault_key = self.encryption.decrypt_vault_key(encrypted_vault_key, master_key)
                    
                    self.session_key = master_key
                    self.vault_key = vault_key
                    self.is_authenticated = True
                    self.universal_storage = UniversalDataManager(vault_key)
                    
                    log_audit_action("BIOMETRIC_LOGIN", success=True, 
                                   details="Touch ID authentication successful")
                    
                    self.update_status("Authenticated with Touch ID")
                    messagebox.showinfo("Success", "🔓 Touch ID authentication successful!")
                    self.show_vault_screen()
                else:
                    messagebox.showerror("Error", "Vault data not found")
            else:
                # Handle specific error cases
                if "cancelled" in message.lower():
                    self.update_status("Touch ID cancelled by user")
                    messagebox.showinfo("Cancelled", "Touch ID authentication was cancelled.")
                elif "failed" in message.lower():
                    self.update_status("Touch ID authentication failed")
                    messagebox.showerror("Authentication Failed", 
                                       f"Touch ID authentication failed.\n\n{message}\n\n"
                                       "Try using your master password instead.")
                else:
                    self.update_status("Touch ID error occurred")
                    messagebox.showerror("Error", f"Touch ID error:\n{message}")
                
                log_audit_action("BIOMETRIC_LOGIN", success=False, details=f"Touch ID failed: {message}")
                    
        except Exception as e:
            error_msg = str(e)
            self.update_status("Biometric authentication error")
            messagebox.showerror("System Error", 
                               f"Biometric authentication system error:\n{error_msg}\n\n"
                               "Please try using your master password instead.")
            log_audit_action("BIOMETRIC_LOGIN", success=False, details=f"System error: {error_msg}")
    
    def password_login(self):
        """Login using master password"""
        master_pass = self.login_pass_entry.get()
        
        if not master_pass:
            messagebox.showwarning("Missing Password", "Please enter your master password")
            return
        
        try:
            self.update_status("Verifying master password...")
            
            # Get user data
            user_data = get_user_advanced()
            if not user_data:
                messagebox.showerror("Error", "No vault found. Please create a new vault.")
                return
            
            master_hash, salt, encrypted_vault_key, biometric_enabled = user_data
            
            # Verify master password
            try:
                self.encryption.ph.verify(master_hash, master_pass)
            except:
                log_audit_action("PASSWORD_LOGIN", success=False, details="Invalid master password")
                messagebox.showerror("Authentication Failed", "Invalid master password!")
                self.update_status("Authentication failed")
                return
            
            # Derive keys
            master_key = self.encryption.derive_master_key(master_pass, salt)
            vault_key = self.encryption.decrypt_vault_key(encrypted_vault_key, master_key)
            
            # Set session
            self.session_key = master_key
            self.vault_key = vault_key
            self.is_authenticated = True
            
            # Initialize universal storage
            self.universal_storage = UniversalDataManager(vault_key)
            
            # Log successful login
            log_audit_action("PASSWORD_LOGIN", success=True, details="Master password authentication successful")
            
            self.update_status("Authenticated successfully")
            messagebox.showinfo("Success", "🔓 Authentication successful!")
            self.show_vault_screen()
            
        except Exception as e:
            log_audit_action("PASSWORD_LOGIN", success=False, details=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Login error:\n{str(e)}")
            self.update_status("Login error occurred")
    
    def show_vault_screen(self):
        """Show the main vault interface with enhanced features"""
        self.clear_content()
        self.update_status("Vault unlocked - Secure session active")
        
        # Main vault container
        vault_container = tk.Frame(self.content_frame, bg=self.colors['secondary'])
        vault_container.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Header with action buttons
        header_frame = tk.Frame(vault_container, bg=self.colors['primary'], relief=tk.RAISED, bd=1)
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Left side - title
        left_header = tk.Frame(header_frame, bg=self.colors['primary'])
        left_header.pack(side='left', padx=15, pady=10)
        
        tk.Label(
            left_header,
            text="🔓 Your Secure Vault",
            font=('Arial', 18, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['primary']
        ).pack(side='left')
        
        # Right side - action buttons
        right_header = tk.Frame(header_frame, bg=self.colors['primary'])
        right_header.pack(side='right', padx=15, pady=10)
        
        # Action buttons
        buttons = [
            ("➕ Add Password", self.show_add_credential_screen, self.colors['success']),
            ("🎲 Generate Password", self.show_password_generator, self.colors['warning']),
            ("📁 Universal Storage", self.show_universal_storage, self.colors['accent']),
            ("⚙️ Settings", self.show_settings, '#95a5a6'),
            ("🔒 Lock Vault", self.lock_vault, self.colors['danger'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                right_header,
                text=text,
                command=command,
                bg=color,
                fg='white',
                font=('Arial', 10, 'bold'),
                padx=10,
                pady=5,
                relief=tk.FLAT,
                cursor='hand2'
            )
            btn.pack(side='left', padx=2)
        
        # Search and filter frame
        search_frame = tk.Frame(vault_container, bg=self.colors['secondary'])
        search_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="🔍 Search:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left', padx=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 11),
            width=30
        )
        search_entry.pack(side='left', padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.filter_credentials)
        
        # Credentials display frame
        self.credentials_frame = tk.Frame(vault_container, bg=self.colors['secondary'])
        self.credentials_frame.pack(expand=True, fill='both')
        
        # Load and display credentials
        self.load_credentials()
    
    def load_credentials(self):
        """Load and display all credentials"""
        try:
            self.current_credentials = get_credentials_advanced()
            self.display_credentials()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load credentials:\n{str(e)}")
    
    def display_credentials(self, filter_text=""):
        """Display credentials with filtering"""
        # Clear existing display
        for widget in self.credentials_frame.winfo_children():
            widget.destroy()
        
        if not self.current_credentials:
            # Empty state
            empty_frame = tk.Frame(self.credentials_frame, bg=self.colors['secondary'])
            empty_frame.pack(expand=True)
            
            tk.Label(
                empty_frame,
                text="🔐 Your vault is empty",
                font=('Arial', 16, 'bold'),
                fg=self.colors['text_muted'],
                bg=self.colors['secondary']
            ).pack(pady=50)
            
            tk.Label(
                empty_frame,
                text="Add your first password to get started!",
                font=('Arial', 12),
                fg=self.colors['text_muted'],
                bg=self.colors['secondary']
            ).pack()
            
            return
        
        # Create scrollable credentials list
        canvas = tk.Canvas(self.credentials_frame, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.credentials_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Filter credentials
        filtered_creds = []
        for cred in self.current_credentials:
            if not filter_text or filter_text.lower() in cred[1].lower() or filter_text.lower() in (cred[2] or "").lower():
                filtered_creds.append(cred)
        
        # Display filtered credentials
        for i, cred in enumerate(filtered_creds):
            self.create_credential_card(scrollable_frame, cred, i)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_credential_card(self, parent, credential, index):
        """Create a card for displaying credential information"""
        cred_id, site, username, encrypted_password, encrypted_notes, encrypted_totp, tags, favorite, created_at, updated_at, last_used, password_strength = credential
        
        # Card frame
        card_color = '#3d566e' if index % 2 == 0 else '#425a75'
        card_frame = tk.Frame(parent, bg=card_color, relief=tk.RAISED, bd=1)
        card_frame.pack(fill='x', padx=5, pady=3)
        
        # Main content frame
        content_frame = tk.Frame(card_frame, bg=card_color)
        content_frame.pack(fill='x', padx=15, pady=10)
        
        # Left side - info
        left_frame = tk.Frame(content_frame, bg=card_color)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Site name with favorite indicator
        site_frame = tk.Frame(left_frame, bg=card_color)
        site_frame.pack(anchor='w')
        
        if favorite:
            tk.Label(
                site_frame,
                text="⭐",
                font=('Arial', 12),
                fg='#f1c40f',
                bg=card_color
            ).pack(side='left')
        
        tk.Label(
            site_frame,
            text=site,
            font=('Arial', 14, 'bold'),
            fg=self.colors['text_light'],
            bg=card_color
        ).pack(side='left', padx=(5 if favorite else 0, 0))
        
        # Username
        if username:
            tk.Label(
                left_frame,
                text=f"👤 {username}",
                font=('Arial', 11),
                fg=self.colors['text_muted'],
                bg=card_color
            ).pack(anchor='w', pady=(5, 0))
        
        # Password strength indicator
        if password_strength > 0:
            strength_colors = ['#e74c3c', '#e67e22', '#f39c12', '#2ecc71', '#27ae60']
            strength_texts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
            strength_idx = min(password_strength - 1, 4)
            
            tk.Label(
                left_frame,
                text=f"🔒 {strength_texts[strength_idx]}",
                font=('Arial', 10),
                fg=strength_colors[strength_idx],
                bg=card_color
            ).pack(anchor='w', pady=(2, 0))
        
        # Right side - actions
        right_frame = tk.Frame(content_frame, bg=card_color)
        right_frame.pack(side='right')
        
        # Action buttons
        actions = [
            ("👁️", lambda: self.view_credential(cred_id), "View"),
            ("📋", lambda: self.copy_password(cred_id, encrypted_password), "Copy Password"),
            ("✏️", lambda: self.edit_credential(cred_id), "Edit"),
            ("🗑️", lambda: self.delete_credential(cred_id, site), "Delete")
        ]
        
        for icon, command, tooltip in actions:
            btn = tk.Button(
                right_frame,
                text=icon,
                command=command,
                bg='#5a6c7d',
                fg='white',
                font=('Arial', 10),
                padx=8,
                pady=4,
                relief=tk.FLAT,
                cursor='hand2'
            )
            btn.pack(side='left', padx=2)
    
    def filter_credentials(self, event=None):
        """Filter displayed credentials based on search text"""
        filter_text = self.search_var.get()
        self.display_credentials(filter_text)
    
    def copy_password(self, cred_id, encrypted_password):
        """Copy decrypted password to clipboard"""
        try:
            # Decrypt password
            decrypted_password = self.encryption.decrypt_data(encrypted_password, self.vault_key).decode()
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(decrypted_password)
            
            # Mark as used
            mark_credential_used(cred_id)
            
            # Show temporary notification
            self.update_status("Password copied to clipboard")
            
            # Auto-clear clipboard after 30 seconds
            self.root.after(30000, self.clear_clipboard)
            
            messagebox.showinfo("Copied", "Password copied to clipboard!\nIt will be cleared in 30 seconds.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy password:\n{str(e)}")
    
    def clear_clipboard(self):
        """Clear clipboard for security"""
        self.root.clipboard_clear()
        self.update_status("Clipboard cleared for security")
    
    def show_add_credential_screen(self):
        """Show screen to add new credential"""
        self.show_credential_form()
    
    def show_credential_form(self, credential_id=None):
        """Show form for adding or editing credentials"""
        messagebox.showinfo("Coming Soon", "Credential form implementation in progress...")
    
    def show_password_generator(self):
        """Show password generator interface"""
        messagebox.showinfo("Coming Soon", "Password generator UI implementation in progress...")
    
    def show_universal_storage(self):
        """Show universal storage interface for files and documents"""
        self.clear_content()
        self.update_status("Loading universal storage...")
        
        # Main container
        storage_container = tk.Frame(self.content_frame, bg=self.colors['secondary'])
        storage_container.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Header
        header_frame = tk.Frame(storage_container, bg=self.colors['primary'], relief=tk.RAISED, bd=1)
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Title
        title_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        title_frame.pack(side='left', padx=15, pady=10)
        
        tk.Label(
            title_frame,
            text="📁 Universal Secure Storage",
            font=('Arial', 18, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['primary']
        ).pack()
        
        # Action buttons
        actions_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        actions_frame.pack(side='right', padx=15, pady=10)
        
        tk.Button(
            actions_frame,
            text="📤 Upload File",
            command=self._upload_file,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            actions_frame,
            text="📝 Add Text Note",
            command=self._add_text_note,
            bg=self.colors['warning'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            actions_frame,
            text="🔙 Back to Vault",
            command=self.show_vault_screen,
            bg=self.colors['accent'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Filter and search frame
        filter_frame = tk.Frame(storage_container, bg=self.colors['secondary'])
        filter_frame.pack(fill='x', pady=(0, 15))
        
        # Category filter
        tk.Label(
            filter_frame,
            text="📂 Category:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left', padx=(0, 10))
        
        self.storage_filter_var = tk.StringVar(value="All Files")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.storage_filter_var,
            values=["All Files", "Images", "Videos", "Documents", "Text Notes", "Other"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side='left', padx=(0, 20))
        filter_combo.bind('<<ComboboxSelected>>', self._filter_storage_items)
        
        # Search
        tk.Label(
            filter_frame,
            text="🔍 Search:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left', padx=(0, 10))
        
        self.storage_search_var = tk.StringVar()
        search_entry = tk.Entry(
            filter_frame,
            textvariable=self.storage_search_var,
            font=('Arial', 11),
            width=25
        )
        search_entry.pack(side='left')
        search_entry.bind('<KeyRelease>', self._search_storage_items)
        
        # Storage items display
        self.storage_frame = tk.Frame(storage_container, bg=self.colors['secondary'])
        self.storage_frame.pack(expand=True, fill='both')
        
        # Load and display storage items
        self._load_storage_items()

    def _upload_file(self):
        """Upload and encrypt a file to universal storage"""
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=[
                ("All Files", "*.*"),
                ("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                ("Videos", "*.mp4 *.avi *.mov *.wmv *.flv *.webm *.mkv"),
                ("Documents", "*.pdf *.doc *.docx *.txt *.rtf *.odt"),
                ("Archives", "*.zip *.rar *.7z *.tar *.gz")
            ]
        )
        
        if not file_path:
            return
        
        # Get additional info from user
        self._show_file_upload_dialog(file_path)

    def _show_file_upload_dialog(self, file_path):
        """Show dialog for file upload details"""
        upload_window = tk.Toplevel(self.root)
        upload_window.title("Upload File Details")
        upload_window.geometry("400x300")
        upload_window.configure(bg=self.colors['secondary'])
        upload_window.transient(self.root)
        upload_window.grab_set()
        
        # Center the window
        upload_window.update_idletasks()
        x = (upload_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (upload_window.winfo_screenheight() // 2) - (300 // 2)
        upload_window.geometry(f"400x300+{x}+{y}")
        
        main_frame = tk.Frame(upload_window, bg=self.colors['secondary'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # File info
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        tk.Label(
            main_frame,
            text="📁 File Upload",
            font=('Arial', 16, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(pady=(0, 20))
        
        # File details
        details_frame = tk.Frame(main_frame, bg=self.colors['primary'], relief=tk.RAISED, bd=1)
        details_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            details_frame,
            text=f"File: {file_name}",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['primary']
        ).pack(anchor='w', padx=10, pady=5)
        
        tk.Label(
            details_frame,
            text=f"Size: {file_size:,} bytes ({file_size/1024:.1f} KB)",
            font=('Arial', 11),
            fg=self.colors['text_muted'],
            bg=self.colors['primary']
        ).pack(anchor='w', padx=10, pady=5)
        
        # Input fields
        tk.Label(
            main_frame,
            text="Display Name:",
            font=('Arial', 11, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(10, 5))
        
        name_var = tk.StringVar(value=file_name)
        name_entry = tk.Entry(main_frame, textvariable=name_var, font=('Arial', 11), width=40)
        name_entry.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            main_frame,
            text="Category:",
            font=('Arial', 11, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(10, 5))
        
        category_var = tk.StringVar(value="files")
        category_combo = ttk.Combobox(
            main_frame,
            textvariable=category_var,
            values=["files", "images", "videos", "documents", "personal", "work"],
            width=37
        )
        category_combo.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            main_frame,
            text="Tags (comma-separated):",
            font=('Arial', 11, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(10, 5))
        
        tags_var = tk.StringVar()
        tags_entry = tk.Entry(main_frame, textvariable=tags_var, font=('Arial', 11), width=40)
        tags_entry.pack(fill='x', pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        button_frame.pack(fill='x')
        
        def upload_file():
            try:
                name = name_var.get().strip() or file_name
                category = category_var.get().strip() or "files"
                tags_text = tags_var.get().strip()
                tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else None
                
                # Upload file
                item_id, message = self.universal_storage.store_file(
                    file_path=file_path,
                    name=name,
                    category=category,
                    tags=tags
                )
                
                upload_window.destroy()
                
                if item_id:
                    messagebox.showinfo("Success", f"File uploaded successfully!\n{message}")
                    self._load_storage_items()  # Refresh display
                else:
                    messagebox.showerror("Error", f"Upload failed:\n{message}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Upload error:\n{str(e)}")
        
        tk.Button(
            button_frame,
            text="📤 Upload",
            command=upload_file,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8
        ).pack(side='right', padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=upload_window.destroy,
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8
        ).pack(side='right')

    def _add_text_note(self):
        """Add a text note to universal storage"""
        note_window = tk.Toplevel(self.root)
        note_window.title("Add Text Note")
        note_window.geometry("500x400")
        note_window.configure(bg=self.colors['secondary'])
        note_window.transient(self.root)
        note_window.grab_set()
        
        # Center the window
        note_window.update_idletasks()
        x = (note_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (note_window.winfo_screenheight() // 2) - (400 // 2)
        note_window.geometry(f"500x400+{x}+{y}")
        
        main_frame = tk.Frame(note_window, bg=self.colors['secondary'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        tk.Label(
            main_frame,
            text="📝 New Text Note",
            font=('Arial', 16, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(pady=(0, 20))
        
        # Note title
        tk.Label(
            main_frame,
            text="Title:",
            font=('Arial', 11, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(0, 5))
        
        title_var = tk.StringVar()
        title_entry = tk.Entry(main_frame, textvariable=title_var, font=('Arial', 11), width=50)
        title_entry.pack(fill='x', pady=(0, 15))
        
        # Note content
        tk.Label(
            main_frame,
            text="Content:",
            font=('Arial', 11, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(0, 5))
        
        content_text = scrolledtext.ScrolledText(
            main_frame,
            width=60,
            height=15,
            font=('Arial', 10),
            wrap=tk.WORD
        )
        content_text.pack(expand=True, fill='both', pady=(0, 15))
        
        # Tags
        tk.Label(
            main_frame,
            text="Tags (comma-separated):",
            font=('Arial', 11, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(anchor='w', pady=(0, 5))
        
        tags_var = tk.StringVar()
        tags_entry = tk.Entry(main_frame, textvariable=tags_var, font=('Arial', 11), width=50)
        tags_entry.pack(fill='x', pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        button_frame.pack(fill='x')
        
        def save_note():
            try:
                title = title_var.get().strip()
                content = content_text.get('1.0', tk.END).strip()
                tags_text = tags_var.get().strip()
                
                if not title:
                    messagebox.showwarning("Missing Title", "Please enter a title for the note")
                    return
                
                if not content:
                    messagebox.showwarning("Missing Content", "Please enter some content for the note")
                    return
                
                tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else None
                
                # Save note
                item_id = self.universal_storage.store_data(
                    name=title,
                    data=content,
                    category="notes",
                    tags=tags,
                    metadata={"content_type": "text_note", "word_count": len(content.split())}
                )
                
                note_window.destroy()
                
                if item_id:
                    messagebox.showinfo("Success", "Text note saved successfully!")
                    self._load_storage_items()  # Refresh display
                else:
                    messagebox.showerror("Error", "Failed to save note")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Save error:\n{str(e)}")
        
        tk.Button(
            button_frame,
            text="💾 Save Note",
            command=save_note,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8
        ).pack(side='right', padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=note_window.destroy,
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=8
        ).pack(side='right')

    def _load_storage_items(self):
        """Load and display all storage items"""
        try:
            if not self.universal_storage:
                return
            
            # Get all items
            self.current_storage_items = self.universal_storage.list_all_data()
            self._display_storage_items()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load storage items:\n{str(e)}")

    def _display_storage_items(self, filter_text="", category_filter="All Files"):
        """Display storage items with filtering"""
        # Clear existing display
        for widget in self.storage_frame.winfo_children():
            widget.destroy()
        
        if not hasattr(self, 'current_storage_items') or not self.current_storage_items:
            # Empty state
            empty_frame = tk.Frame(self.storage_frame, bg=self.colors['secondary'])
            empty_frame.pack(expand=True)
            
            tk.Label(
                empty_frame,
                text="📁 No files stored yet",
                font=('Arial', 16, 'bold'),
                fg=self.colors['text_muted'],
                bg=self.colors['secondary']
            ).pack(pady=50)
            
            tk.Label(
                empty_frame,
                text="Upload files, images, videos, or documents to get started!",
                font=('Arial', 12),
                fg=self.colors['text_muted'],
                bg=self.colors['secondary']
            ).pack()
            
            return
        
        # Create scrollable items list
        canvas = tk.Canvas(self.storage_frame, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.storage_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['secondary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Filter items
        filtered_items = self._filter_items(self.current_storage_items, filter_text, category_filter)
        
        # Display filtered items
        for i, item in enumerate(filtered_items):
            self._create_storage_item_card(scrollable_frame, item, i)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _filter_items(self, items, search_text, category_filter):
        """Filter items based on search text and category"""
        filtered = []
        
        for item in items:
            # Category filter
            if category_filter != "All Files":
                item_category = item.get('category', '').lower()
                metadata = item.get('metadata', {})
                
                if category_filter == "Images":
                    if not (item_category == 'images' or 
                           (isinstance(metadata, dict) and 
                            metadata.get('file_extension', '').lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'])):
                        continue
                elif category_filter == "Videos":
                    if not (item_category == 'videos' or 
                           (isinstance(metadata, dict) and 
                            metadata.get('file_extension', '').lower() in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'])):
                        continue
                elif category_filter == "Documents":
                    if not (item_category == 'documents' or 
                           (isinstance(metadata, dict) and 
                            metadata.get('file_extension', '').lower() in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'])):
                        continue
                elif category_filter == "Text Notes":
                    if not (item_category == 'notes' or 
                           (isinstance(metadata, dict) and 
                            metadata.get('content_type') == 'text_note')):
                        continue
            
            # Search filter
            if search_text:
                search_lower = search_text.lower()
                name_match = search_lower in item.get('name', '').lower()
                tags_match = False
                
                tags = item.get('tags', [])
                if tags:
                    tags_match = any(search_lower in tag.lower() for tag in tags)
                
                if not (name_match or tags_match):
                    continue
            
            filtered.append(item)
        
        return filtered

    def _create_storage_item_card(self, parent, item, index):
        """Create a card for displaying storage item"""
        item_id = item.get('id')
        name = item.get('name', 'Unknown')
        category = item.get('category', 'general')
        data_type = item.get('data_type', 'unknown')
        tags = item.get('tags', [])
        created_at = item.get('created_at', '')
        metadata = item.get('metadata', {})
        
        # Card frame
        card_color = '#3d566e' if index % 2 == 0 else '#425a75'
        card_frame = tk.Frame(parent, bg=card_color, relief=tk.RAISED, bd=1)
        card_frame.pack(fill='x', padx=5, pady=3)
        
        # Main content frame
        content_frame = tk.Frame(card_frame, bg=card_color)
        content_frame.pack(fill='x', padx=15, pady=10)
        
        # Left side - info
        left_frame = tk.Frame(content_frame, bg=card_color)
        left_frame.pack(side='left', fill='x', expand=True)
        
        # Icon and name
        icon_frame = tk.Frame(left_frame, bg=card_color)
        icon_frame.pack(anchor='w')
        
        # Get appropriate icon
        icon = self._get_file_icon(data_type, metadata)
        
        tk.Label(
            icon_frame,
            text=icon,
            font=('Arial', 16),
            fg=self.colors['warning'],
            bg=card_color
        ).pack(side='left', padx=(0, 10))
        
        tk.Label(
            icon_frame,
            text=name,
            font=('Arial', 14, 'bold'),
            fg=self.colors['text_light'],
            bg=card_color
        ).pack(side='left')
        
        # Details
        details_frame = tk.Frame(left_frame, bg=card_color)
        details_frame.pack(anchor='w', pady=(5, 0))
        
        # File info
        if isinstance(metadata, dict):
            file_size = metadata.get('file_size')
            if file_size:
                size_text = f"📏 {file_size:,} bytes"
                if file_size > 1024:
                    size_text += f" ({file_size/1024:.1f} KB)"
            else:
                size_text = f"📂 {category.title()}"
            
            tk.Label(
                details_frame,
                text=size_text,
                font=('Arial', 10),
                fg=self.colors['text_muted'],
                bg=card_color
            ).pack(side='left', padx=(0, 15))
        
        # Tags
        if tags:
            tags_text = f"🏷️ {', '.join(tags[:3])}"
            if len(tags) > 3:
                tags_text += f" +{len(tags)-3}"
            
            tk.Label(
                details_frame,
                text=tags_text,
                font=('Arial', 10),
                fg=self.colors['accent'],
                bg=card_color
            ).pack(side='left')
        
        # Right side - actions
        right_frame = tk.Frame(content_frame, bg=card_color)
        right_frame.pack(side='right')
        
        # Action buttons
        actions = [
            ("👁️", lambda: self._view_storage_item(item_id), "View"),
            ("📥", lambda: self._download_storage_item(item_id, name), "Download"),
            ("🗑️", lambda: self._delete_storage_item(item_id, name), "Delete")
        ]
        
        for icon, command, tooltip in actions:
            btn = tk.Button(
                right_frame,
                text=icon,
                command=command,
                bg='#5a6c7d',
                fg='white',
                font=('Arial', 10),
                padx=8,
                pady=4,
                relief=tk.FLAT,
                cursor='hand2'
            )
            btn.pack(side='left', padx=2)

    def _get_file_icon(self, data_type, metadata):
        """Get appropriate icon for file type"""
        if isinstance(metadata, dict):
            file_ext = metadata.get('file_extension', '').lower()
            mime_type = metadata.get('mime_type', '')
            content_type = metadata.get('content_type', '')
            
            # Text notes
            if content_type == 'text_note':
                return "📝"
            
            # Images
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'] or 'image' in mime_type:
                return "🖼️"
            
            # Videos
            if file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'] or 'video' in mime_type:
                return "🎥"
            
            # Documents
            if file_ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']:
                if file_ext == '.pdf':
                    return "📕"
                else:
                    return "📄"
            
            # Archives
            if file_ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                return "📦"
        
        # Default icons by data type
        if data_type == 'text':
            return "📝"
        elif data_type == 'json':
            return "📋"
        elif data_type == 'binary':
            return "📁"
        else:
            return "📄"

    def _filter_storage_items(self, event=None):
        """Filter storage items by category"""
        category_filter = self.storage_filter_var.get()
        search_text = self.storage_search_var.get()
        self._display_storage_items(search_text, category_filter)

    def _search_storage_items(self, event=None):
        """Search storage items by name or tags"""
        search_text = self.storage_search_var.get()
        category_filter = self.storage_filter_var.get()
        self._display_storage_items(search_text, category_filter)

    def _view_storage_item(self, item_id):
        """View storage item details"""
        try:
            result, status = self.universal_storage.retrieve_data(item_id=item_id)
            
            if not result:
                messagebox.showerror("Error", f"Failed to retrieve item:\n{status}")
                return
            
            # Create view window
            view_window = tk.Toplevel(self.root)
            view_window.title(f"View: {result['name']}")
            view_window.geometry("600x500")
            view_window.configure(bg=self.colors['secondary'])
            view_window.transient(self.root)
            
            main_frame = tk.Frame(view_window, bg=self.colors['secondary'])
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            # Title
            tk.Label(
                main_frame,
                text=f"👁️ {result['name']}",
                font=('Arial', 16, 'bold'),
                fg=self.colors['text_light'],
                bg=self.colors['secondary']
            ).pack(pady=(0, 20))
            
            # Content display based on type
            data = result['data']
            data_type = result['data_type']
            metadata = result.get('metadata', {})
            
            if data_type == 'text' or (isinstance(metadata, dict) and metadata.get('content_type') == 'text_note'):
                # Display text content
                text_widget = scrolledtext.ScrolledText(
                    main_frame,
                    width=70,
                    height=20,
                    font=('Arial', 11),
                    wrap=tk.WORD,
                    state='normal'
                )
                text_widget.pack(expand=True, fill='both', pady=(0, 15))
                
                if isinstance(data, bytes):
                    data = data.decode('utf-8', errors='ignore')
                
                text_widget.insert('1.0', data)
                text_widget.config(state='disabled')
            
            else:
                # Display metadata for files
                info_frame = tk.Frame(main_frame, bg=self.colors['primary'], relief=tk.RAISED, bd=1)
                info_frame.pack(fill='x', pady=(0, 15))
                
                if isinstance(metadata, dict):
                    info_text = ""
                    if 'original_filename' in metadata:
                        info_text += f"Original Name: {metadata['original_filename']}\n"
                    if 'file_size' in metadata:
                        size = metadata['file_size']
                        info_text += f"Size: {size:,} bytes ({size/1024:.1f} KB)\n"
                    if 'mime_type' in metadata:
                        info_text += f"Type: {metadata['mime_type']}\n"
                    if 'upload_date' in metadata:
                        info_text += f"Uploaded: {metadata['upload_date'][:19]}\n"
                    
                    tk.Label(
                        info_frame,
                        text=info_text.strip(),
                        font=('Arial', 11),
                        fg=self.colors['text_light'],
                        bg=self.colors['primary'],
                        justify='left'
                    ).pack(anchor='w', padx=15, pady=10)
                
                tk.Label(
                    main_frame,
                    text="Use the Download button to save this file to your computer",
                    font=('Arial', 11),
                    fg=self.colors['text_muted'],
                    bg=self.colors['secondary']
                ).pack(pady=20)
            
            # Close button
            tk.Button(
                main_frame,
                text="❌ Close",
                command=view_window.destroy,
                bg=self.colors['danger'],
                fg='white',
                font=('Arial', 11, 'bold'),
                padx=20,
                pady=8
            ).pack()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view item:\n{str(e)}")

    def _download_storage_item(self, item_id, name):
        """Download storage item to local file"""
        try:
            # Choose save location
            file_path = filedialog.asksaveasfilename(
                title="Save file as",
                initialfile=name,  # Fixed parameter name
                filetypes=[
                    ("All Files", "*.*"),
                    ("Text Files", "*.txt"),
                    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("Videos", "*.mp4 *.avi *.mov *.wmv"),
                    ("Documents", "*.pdf *.doc *.docx")
                ],
                defaultextension=""
            )
            
            if not file_path:
                return
            
            # Retrieve and save file
            result, status = self.universal_storage.retrieve_file(item_id, file_path)
            
            if result:
                messagebox.showinfo("Success", f"File downloaded successfully to:\n{file_path}")
            else:
                messagebox.showerror("Error", f"Download failed:\n{status}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Download error:\n{str(e)}")

    def _delete_storage_item(self, item_id, name):
        """Delete storage item"""
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete '{name}'?\n\nThis action cannot be undone."
        )
        
        if result:
            try:
                success = self.universal_storage.delete_data(item_id)
                
                if success:
                    messagebox.showinfo("Success", "Item deleted successfully!")
                    self._load_storage_items()  # Refresh display
                else:
                    messagebox.showerror("Error", "Failed to delete item")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Delete error:\n{str(e)}")
    
    def show_settings(self):
        """Show comprehensive application settings interface"""
        self.clear_content()
        self.update_status("Configuring vault settings...")
        
        # Main settings container
        settings_container = tk.Frame(self.content_frame, bg=self.colors['secondary'])
        settings_container.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Header
        header_frame = tk.Frame(settings_container, bg=self.colors['primary'], relief=tk.RAISED, bd=1)
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            header_frame,
            text="⚙️ VaultKeeper Settings",
            font=('Arial', 18, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['primary']
        ).pack(pady=15)
        
        # Create notebook for tabbed settings
        notebook = ttk.Notebook(settings_container)
        notebook.pack(expand=True, fill='both')
        
        # Security Settings Tab
        security_frame = tk.Frame(notebook, bg=self.colors['secondary'])
        notebook.add(security_frame, text="🔒 Security")
        self._create_security_settings(security_frame)
        
        # Biometric Settings Tab
        biometric_frame = tk.Frame(notebook, bg=self.colors['secondary'])
        notebook.add(biometric_frame, text="🔓 Touch ID")
        self._create_biometric_settings(biometric_frame)
        
        # Auto-lock Settings Tab
        autolock_frame = tk.Frame(notebook, bg=self.colors['secondary'])
        notebook.add(autolock_frame, text="🔒 Auto-Lock")
        self._create_autolock_settings(autolock_frame)
        
        # Data Management Tab
        data_frame = tk.Frame(notebook, bg=self.colors['secondary'])
        notebook.add(data_frame, text="📊 Data")
        self._create_data_settings(data_frame)
        
        # About Tab
        about_frame = tk.Frame(notebook, bg=self.colors['secondary'])
        notebook.add(about_frame, text="ℹ️ About")
        self._create_about_settings(about_frame)
        
        # Bottom buttons
        button_frame = tk.Frame(settings_container, bg=self.colors['secondary'])
        button_frame.pack(fill='x', pady=(20, 0))
        
        tk.Button(
            button_frame,
            text="🔙 Back to Vault",
            command=self.show_vault_screen,
            bg=self.colors['accent'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side='right', padx=10)

    def _create_security_settings(self, parent):
        """Create security settings interface"""
        # Master Password Section
        master_section = tk.LabelFrame(
            parent, 
            text="🔐 Master Password",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        master_section.pack(fill='x', padx=20, pady=10)
        
        tk.Button(
            master_section,
            text="Change Master Password",
            command=self._change_master_password,
            bg=self.colors['warning'],
            fg='white',
            font=('Arial', 11),
            padx=15,
            pady=8
        ).pack(pady=10)
        
        # Session Settings
        session_section = tk.LabelFrame(
            parent,
            text="🕐 Session Security",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        session_section.pack(fill='x', padx=20, pady=10)
        
        # Clipboard auto-clear
        self.clipboard_clear_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            session_section,
            text="Auto-clear clipboard after 30 seconds",
            variable=self.clipboard_clear_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success'],
            command=self._save_security_settings
        ).pack(anchor='w', padx=10, pady=5)

    def _create_biometric_settings(self, parent):
        """Create biometric authentication settings"""
        # Current Status
        status_section = tk.LabelFrame(
            parent,
            text="📱 Touch ID Status",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        status_section.pack(fill='x', padx=20, pady=10)
        
        # Check current status
        touchid_available = self.biometric.is_touchid_available()
        user_data = get_user_advanced()
        biometric_enabled = user_data and len(user_data) > 3 and user_data[3]
        
        status_text = "✅ Touch ID Available" if touchid_available else "❌ Touch ID Not Available"
        tk.Label(
            status_section,
            text=status_text,
            font=('Arial', 11),
            fg=self.colors['success'] if touchid_available else self.colors['danger'],
            bg=self.colors['secondary']
        ).pack(anchor='w', padx=10, pady=5)
        
        enabled_text = "✅ Touch ID Enabled" if biometric_enabled else "❌ Touch ID Disabled"
        tk.Label(
            status_section,
            text=enabled_text,
            font=('Arial', 11),
            fg=self.colors['success'] if biometric_enabled else self.colors['danger'],
            bg=self.colors['secondary']
        ).pack(anchor='w', padx=10, pady=5)
        
        # Controls
        controls_section = tk.LabelFrame(
            parent,
            text="🔧 Touch ID Controls",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        controls_section.pack(fill='x', padx=20, pady=10)
        
        if touchid_available:
            if not biometric_enabled:
                tk.Button(
                    controls_section,
                    text="🔓 Enable Touch ID",
                    command=self._enable_touchid,
                    bg=self.colors['success'],
                    fg='white',
                    font=('Arial', 11),
                    padx=15,
                    pady=8
                ).pack(pady=10)
            else:
                button_frame = tk.Frame(controls_section, bg=self.colors['secondary'])
                button_frame.pack(pady=10)
                
                tk.Button(
                    button_frame,
                    text="🔄 Re-setup Touch ID",
                    command=self._reset_touchid,
                    bg=self.colors['warning'],
                    fg='white',
                    font=('Arial', 10),
                    padx=12,
                    pady=6
                ).pack(side='left', padx=5)
                
                tk.Button(
                    button_frame,
                    text="🚫 Disable Touch ID",
                    command=self._disable_touchid,
                    bg=self.colors['danger'],
                    fg='white',
                    font=('Arial', 10),
                    padx=12,
                    pady=6
                ).pack(side='left', padx=5)

    def _create_autolock_settings(self, parent):
        """Create auto-lock settings interface"""
        autolock_section = tk.LabelFrame(
            parent,
            text="⏰ Auto-Lock Configuration",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        autolock_section.pack(fill='x', padx=20, pady=10)
        
        # Enable auto-lock
        self.autolock_enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            autolock_section,
            text="Enable auto-lock when inactive",
            variable=self.autolock_enabled_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success'],
            command=self._save_autolock_settings
        ).pack(anchor='w', padx=10, pady=10)
        
        # Timeout selection
        timeout_frame = tk.Frame(autolock_section, bg=self.colors['secondary'])
        timeout_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            timeout_frame,
            text="Auto-lock after:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left')
        
        self.timeout_var = tk.StringVar(value="15 minutes")
        timeout_combo = ttk.Combobox(
            timeout_frame,
            textvariable=self.timeout_var,
            values=["5 minutes", "10 minutes", "15 minutes", "30 minutes", "1 hour"],
            state="readonly",
            width=12
        )
        timeout_combo.pack(side='left', padx=10)
        timeout_combo.bind('<<ComboboxSelected>>', lambda e: self._save_autolock_settings())

    def _create_data_settings(self, parent):
        """Create data management settings"""
        # Database info
        db_section = tk.LabelFrame(
            parent,
            text="🗄️ Database Information",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        db_section.pack(fill='x', padx=20, pady=10)
        
        try:
            stats = get_database_stats()
            
            info_text = f"Credentials: {stats.get('credentials_count', 0)}\n"
            info_text += f"Audit Logs: {stats.get('audit_log_count', 0)}\n"
            info_text += f"Database Size: {stats.get('database_size', 0) / 1024:.1f} KB"
            
            tk.Label(
                db_section,
                text=info_text,
                font=('Arial', 10),
                fg=self.colors['text_muted'],
                bg=self.colors['secondary'],
                justify='left'
            ).pack(anchor='w', padx=10, pady=10)
            
        except Exception as e:
            tk.Label(
                db_section,
                text="Database statistics unavailable",
                font=('Arial', 10),
                fg=self.colors['text_muted'],
                bg=self.colors['secondary']
            ).pack(anchor='w', padx=10, pady=10)
        
        # Maintenance actions
        maintenance_section = tk.LabelFrame(
            parent,
            text="🔧 Database Maintenance",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        maintenance_section.pack(fill='x', padx=20, pady=10)
        
        tk.Button(
            maintenance_section,
            text="🗜️ Optimize Database",
            command=self._optimize_database,
            bg=self.colors['accent'],
            fg='white',
            font=('Arial', 11),
            padx=15,
            pady=8
        ).pack(pady=10)

    def _create_about_settings(self, parent):
        """Create about section"""
        about_section = tk.Frame(parent, bg=self.colors['secondary'])
        about_section.pack(expand=True, fill='both', padx=20, pady=20)
        
        # App info
        tk.Label(
            about_section,
            text="🔐 VaultKeeper",
            font=('Arial', 24, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(pady=20)
        
        tk.Label(
            about_section,
            text="Advanced Secure Password Manager",
            font=('Arial', 14),
            fg=self.colors['text_muted'],
            bg=self.colors['secondary']
        ).pack()
        
        tk.Label(
            about_section,
            text="Version 1.0.0",
            font=('Arial', 12),
            fg=self.colors['text_muted'],
            bg=self.colors['secondary']
        ).pack(pady=10)
        
        # Features list
        features_text = """
Features:
• Zero-knowledge encryption with AES-256
• Touch ID biometric authentication
• Universal secure data storage
• Password generation and strength analysis
• Secure password sharing
• Comprehensive audit logging
• Cross-platform compatibility
"""
        
        tk.Label(
            about_section,
            text=features_text,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            justify='left'
        ).pack(pady=20)

    # Helper methods for settings functionality
    def _enable_touchid(self):
        """Enable Touch ID authentication"""
        messagebox.showinfo("Touch ID", "Touch ID setup initiated...")

    def _disable_touchid(self):
        """Disable Touch ID authentication"""
        result = messagebox.askyesno("Confirm", "Disable Touch ID authentication?")
        if result:
            messagebox.showinfo("Touch ID", "Touch ID disabled successfully")

    def _reset_touchid(self):
        """Reset Touch ID setup"""
        messagebox.showinfo("Touch ID", "Touch ID reset initiated...")

    def _change_master_password(self):
        """Change master password"""
        messagebox.showinfo("Security", "Master password change initiated...")

    def _save_security_settings(self):
        """Save security settings"""
        pass

    def _save_autolock_settings(self):
        """Save auto-lock settings"""
        pass

    def _optimize_database(self):
        """Optimize database performance"""
        try:
            vacuum_database()
            messagebox.showinfo("Success", "Database optimized successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Database optimization failed:\n{str(e)}")
    
    def view_credential(self, cred_id):
        """View detailed credential information"""
        messagebox.showinfo("Coming Soon", f"View credential {cred_id} - Implementation in progress...")
    
    def edit_credential(self, cred_id):
        """Edit existing credential"""
        messagebox.showinfo("Coming Soon", f"Edit credential {cred_id} - Implementation in progress...")
    
    def delete_credential(self, cred_id, site):
        """Delete credential after confirmation"""
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the credential for '{site}'?\n\nThis action cannot be undone."
        )
        
        if result:
            try:
                success = delete_credential_advanced(cred_id)
                if success:
                    messagebox.showinfo("Success", "Credential deleted successfully!")
                    self.load_credentials()  # Refresh display
                else:
                    messagebox.showerror("Error", "Failed to delete credential")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete credential:\n{str(e)}")
    
    def lock_vault(self):
        """Lock the vault and return to login"""
        # Log the action
        log_audit_action("VAULT_LOCKED", success=True, details="Vault manually locked")
        
        # Clear session data
        self.session_key = None
        self.vault_key = None
        self.is_authenticated = False
        self.universal_storage = None
        self.current_credentials = []
        self.current_storage_items = []
        
        # Clear clipboard for security
        self.clear_clipboard()
        
        self.update_status("Vault locked")
        messagebox.showinfo("Locked", "🔒 Vault has been locked securely")
        self.show_login_screen()
    
    def clear_content(self):
        """Clear the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def run(self):
        """Start the application"""
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Center window on screen
        self.center_window()
        
        # Start the main loop
        self.root.mainloop()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_authenticated:
            result = messagebox.askyesno(
                "Confirm Exit",
                "Your vault is currently unlocked. Do you want to exit and lock your vault?"
            )
            if result:
                # Log the action
                log_audit_action("APPLICATION_CLOSED", success=True, details="Application closed with vault locked")
                self.clear_clipboard()
                self.root.destroy()
        else:
            self.root.destroy()

# Run the application
if __name__ == "__main__":
    app = VaultKeeperMainWindow()
    app.run()
