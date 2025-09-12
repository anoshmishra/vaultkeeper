# ui/settings_windows.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

class SettingsWindow:
    """Comprehensive settings management window"""
    
    def __init__(self, parent, biometric_auth=None):
        self.parent = parent
        self.biometric = biometric_auth
        self.settings = settings
        
        self.window = tk.Toplevel(parent)
        self.window.title("VaultKeeper Settings")
        self.window.geometry("700x600")
        self.window.configure(bg='#34495e')
        self.window.transient(parent)
        self.window.grab_set()
        
        # Colors
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'text_light': '#ecf0f1',
            'text_muted': '#bdc3c7'
        }
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Setup the settings interface"""
        # Header
        header_frame = tk.Frame(self.window, bg=self.colors['primary'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            header_frame,
            text="⚙️ VaultKeeper Settings",
            font=('Arial', 18, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['primary']
        ).pack(pady=15)
        
        # Main content with notebook
        main_frame = tk.Frame(self.window, bg=self.colors['secondary'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Create notebook for tabbed settings
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill='both')
        
        # Security Tab
        security_frame = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.notebook.add(security_frame, text="🔒 Security")
        self.create_security_tab(security_frame)
        
        # UI Tab
        ui_frame = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.notebook.add(ui_frame, text="🎨 Interface")
        self.create_ui_tab(ui_frame)
        
        # Biometric Tab
        biometric_frame = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.notebook.add(biometric_frame, text="🔓 Biometric")
        self.create_biometric_tab(biometric_frame)
        
        # Backup Tab
        backup_frame = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.notebook.add(backup_frame, text="💾 Backup")
        self.create_backup_tab(backup_frame)
        
        # Advanced Tab
        advanced_frame = tk.Frame(self.notebook, bg=self.colors['secondary'])
        self.notebook.add(advanced_frame, text="⚡ Advanced")
        self.create_advanced_tab(advanced_frame)
        
        # Bottom buttons
        button_frame = tk.Frame(self.window, bg=self.colors['secondary'])
        button_frame.pack(fill='x', pady=20)
        
        tk.Button(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self.reset_to_defaults,
            bg=self.colors['warning'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8
        ).pack(side='right', padx=10)
    
    def create_security_tab(self, parent):
        """Create security settings tab"""
        # Auto-lock settings
        autolock_frame = tk.LabelFrame(
            parent,
            text="🔒 Auto-Lock Settings",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        autolock_frame.pack(fill='x', padx=20, pady=10)
        
        # Auto-lock timeout
        timeout_frame = tk.Frame(autolock_frame, bg=self.colors['secondary'])
        timeout_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            timeout_frame,
            text="Auto-lock timeout (minutes):",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left')
        
        self.autolock_timeout_var = tk.IntVar()
        timeout_spinbox = tk.Spinbox(
            timeout_frame,
            from_=5,
            to=120,
            textvariable=self.autolock_timeout_var,
            width=5
        )
        timeout_spinbox.pack(side='right')
        
        # Clipboard settings
        clipboard_frame = tk.LabelFrame(
            parent,
            text="📋 Clipboard Security",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        clipboard_frame.pack(fill='x', padx=20, pady=10)
        
        # Clipboard clear timeout
        clipboard_timeout_frame = tk.Frame(clipboard_frame, bg=self.colors['secondary'])
        clipboard_timeout_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            clipboard_timeout_frame,
            text="Clear clipboard after (seconds):",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left')
        
        self.clipboard_timeout_var = tk.IntVar()
        clipboard_spinbox = tk.Spinbox(
            clipboard_timeout_frame,
            from_=10,
            to=300,
            textvariable=self.clipboard_timeout_var,
            width=5
        )
        clipboard_spinbox.pack(side='right')
    
    def create_ui_tab(self, parent):
        """Create UI settings tab"""
        # Theme settings
        theme_frame = tk.LabelFrame(
            parent,
            text="🎨 Appearance",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        theme_frame.pack(fill='x', padx=20, pady=10)
        
        # Theme selection
        theme_select_frame = tk.Frame(theme_frame, bg=self.colors['secondary'])
        theme_select_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            theme_select_frame,
            text="Theme:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left')
        
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(
            theme_select_frame,
            textvariable=self.theme_var,
            values=["dark", "light", "system"],
            state="readonly",
            width=10
        )
        theme_combo.pack(side='right')
        
        # Window settings
        window_frame = tk.LabelFrame(
            parent,
            text="🪟 Window Settings",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        window_frame.pack(fill='x', padx=20, pady=10)
        
        self.save_window_position_var = tk.BooleanVar()
        tk.Checkbutton(
            window_frame,
            text="Remember window size and position",
            variable=self.save_window_position_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success']
        ).pack(anchor='w', padx=10, pady=5)
        
        self.show_strength_var = tk.BooleanVar()
        tk.Checkbutton(
            window_frame,
            text="Show password strength indicators",
            variable=self.show_strength_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success']
        ).pack(anchor='w', padx=10, pady=5)
    
    def create_biometric_tab(self, parent):
        """Create biometric settings tab"""
        # Touch ID status
        status_frame = tk.LabelFrame(
            parent,
            text="🔓 Touch ID Status",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        status_frame.pack(fill='x', padx=20, pady=10)
        
        if self.biometric:
            touchid_available = self.biometric.is_touchid_available()
            status_text = "✅ Available" if touchid_available else "❌ Not Available"
            status_color = self.colors['success'] if touchid_available else self.colors['danger']
        else:
            status_text = "❓ Unknown"
            status_color = self.colors['text_muted']
        
        tk.Label(
            status_frame,
            text=f"Touch ID: {status_text}",
            font=('Arial', 11),
            fg=status_color,
            bg=self.colors['secondary']
        ).pack(anchor='w', padx=10, pady=5)
        
        # Touch ID settings
        touchid_frame = tk.LabelFrame(
            parent,
            text="🔧 Touch ID Options",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        touchid_frame.pack(fill='x', padx=20, pady=10)
        
        self.enable_touchid_var = tk.BooleanVar()
        tk.Checkbutton(
            touchid_frame,
            text="Enable Touch ID for vault unlock",
            variable=self.enable_touchid_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success']
        ).pack(anchor='w', padx=10, pady=5)
        
        self.touchid_critical_var = tk.BooleanVar()
        tk.Checkbutton(
            touchid_frame,
            text="Require Touch ID for critical operations",
            variable=self.touchid_critical_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success']
        ).pack(anchor='w', padx=10, pady=5)
    
    def create_backup_tab(self, parent):
        """Create backup settings tab"""
        # Auto-backup settings
        backup_frame = tk.LabelFrame(
            parent,
            text="💾 Automatic Backup",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        backup_frame.pack(fill='x', padx=20, pady=10)
        
        self.auto_backup_var = tk.BooleanVar()
        tk.Checkbutton(
            backup_frame,
            text="Enable automatic backups",
            variable=self.auto_backup_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success']
        ).pack(anchor='w', padx=10, pady=5)
        
        # Backup frequency
        freq_frame = tk.Frame(backup_frame, bg=self.colors['secondary'])
        freq_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            freq_frame,
            text="Backup frequency (days):",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left')
        
        self.backup_frequency_var = tk.IntVar()
        freq_spinbox = tk.Spinbox(
            freq_frame,
            from_=1,
            to=30,
            textvariable=self.backup_frequency_var,
            width=5
        )
        freq_spinbox.pack(side='right')
        
        # Backup location
        location_frame = tk.Frame(backup_frame, bg=self.colors['secondary'])
        location_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            location_frame,
            text="Backup location:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(anchor='w')
        
        self.backup_location_var = tk.StringVar()
        location_entry = tk.Entry(
            location_frame,
            textvariable=self.backup_location_var,
            font=('Arial', 10),
            width=40
        )
        location_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        tk.Button(
            location_frame,
            text="Browse",
            command=self.browse_backup_location,
            bg=self.colors['warning'],
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(side='right')
    
    def create_advanced_tab(self, parent):
        """Create advanced settings tab"""
        # Encryption settings
        encrypt_frame = tk.LabelFrame(
            parent,
            text="🔐 Encryption Settings",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        encrypt_frame.pack(fill='x', padx=20, pady=10)
        
        # Key derivation iterations
        kdf_frame = tk.Frame(encrypt_frame, bg=self.colors['secondary'])
        kdf_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            kdf_frame,
            text="Key derivation iterations:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left')
        
        self.kdf_iterations_var = tk.IntVar()
        kdf_spinbox = tk.Spinbox(
            kdf_frame,
            from_=50000,
            to=500000,
            increment=10000,
            textvariable=self.kdf_iterations_var,
            width=10
        )
        kdf_spinbox.pack(side='right')
        
        # Memory protection
        memory_frame = tk.LabelFrame(
            parent,
            text="🧠 Memory Protection",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        memory_frame.pack(fill='x', padx=20, pady=10)
        
        self.memory_protection_var = tk.BooleanVar()
        tk.Checkbutton(
            memory_frame,
            text="Enable memory protection",
            variable=self.memory_protection_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success']
        ).pack(anchor='w', padx=10, pady=5)
        
        self.secure_delete_var = tk.BooleanVar()
        tk.Checkbutton(
            memory_frame,
            text="Secure delete temporary files",
            variable=self.secure_delete_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success']
        ).pack(anchor='w', padx=10, pady=5)
    
    def load_current_settings(self):
        """Load current settings into UI"""
        # Security settings
        self.autolock_timeout_var.set(self.settings.get('security', 'auto_lock_timeout', 900) // 60)
        self.clipboard_timeout_var.set(self.settings.get('security', 'clipboard_clear_timeout', 30))
        
        # UI settings
        self.theme_var.set(self.settings.get('ui', 'theme', 'dark'))
        self.save_window_position_var.set(self.settings.get('ui', 'auto_save_window_position', True))
        self.show_strength_var.set(self.settings.get('ui', 'show_password_strength', True))
        
        # Biometric settings
        self.enable_touchid_var.set(self.settings.get('biometric', 'enable_touch_id', False))
        self.touchid_critical_var.set(self.settings.get('biometric', 'touch_id_for_critical_operations', False))
        
        # Backup settings
        self.auto_backup_var.set(self.settings.get('backup', 'auto_backup_enabled', True))
        self.backup_frequency_var.set(self.settings.get('backup', 'backup_frequency_days', 7))
        self.backup_location_var.set(self.settings.get('backup', 'backup_location', ''))
        
        # Advanced settings
        self.kdf_iterations_var.set(self.settings.get('advanced', 'key_derivation_iterations', 100000))
        self.memory_protection_var.set(self.settings.get('advanced', 'memory_protection', True))
        self.secure_delete_var.set(self.settings.get('advanced', 'secure_delete', True))
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Security settings
            self.settings.set('security', 'auto_lock_timeout', self.autolock_timeout_var.get() * 60)
            self.settings.set('security', 'clipboard_clear_timeout', self.clipboard_timeout_var.get())
            
            # UI settings
            self.settings.set('ui', 'theme', self.theme_var.get())
            self.settings.set('ui', 'auto_save_window_position', self.save_window_position_var.get())
            self.settings.set('ui', 'show_password_strength', self.show_strength_var.get())
            
            # Biometric settings
            self.settings.set('biometric', 'enable_touch_id', self.enable_touchid_var.get())
            self.settings.set('biometric', 'touch_id_for_critical_operations', self.touchid_critical_var.get())
            
            # Backup settings
            self.settings.set('backup', 'auto_backup_enabled', self.auto_backup_var.get())
            self.settings.set('backup', 'backup_frequency_days', self.backup_frequency_var.get())
            self.settings.set('backup', 'backup_location', self.backup_location_var.get())
            
            # Advanced settings
            self.settings.set('advanced', 'key_derivation_iterations', self.kdf_iterations_var.get())
            self.settings.set('advanced', 'memory_protection', self.memory_protection_var.get())
            self.settings.set('advanced', 'secure_delete', self.secure_delete_var.get())
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{str(e)}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        result = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset all settings to default values?"
        )
        
        if result:
            self.settings.reset_to_defaults()
            self.load_current_settings()
            messagebox.showinfo("Reset", "Settings reset to defaults")
    
    def browse_backup_location(self):
        """Browse for backup directory"""
        directory = filedialog.askdirectory(title="Select Backup Location")
        if directory:
            self.backup_location_var.set(directory)
