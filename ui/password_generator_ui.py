# ui/password_generator_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advanced.password_generator import AdvancedPasswordGenerator
from config.settings import settings

class PasswordGeneratorWindow:
    """Advanced password generator interface"""
    
    def __init__(self, parent, vault_key=None):
        self.parent = parent
        self.vault_key = vault_key
        self.generator = AdvancedPasswordGenerator()
        self._clipboard_secret = None
        self._clipboard_after_id = None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Advanced Password Generator")
        self.window.geometry("500x600")
        self.window.configure(bg='#34495e')
        self.window.resizable(False, False)
        
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
        self.generate_password()  # Generate initial password
    
    def setup_ui(self):
        """Setup the password generator interface"""
        # Header
        header_frame = tk.Frame(self.window, bg=self.colors['primary'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            header_frame,
            text="🎲 Advanced Password Generator",
            font=('Arial', 16, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['primary']
        ).pack(pady=15)
        
        # Main content
        main_frame = tk.Frame(self.window, bg=self.colors['secondary'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Generated password display
        password_frame = tk.LabelFrame(
            main_frame,
            text="Generated Password",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        password_frame.pack(fill='x', pady=10)
        
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(
            password_frame,
            textvariable=self.password_var,
            font=('Courier', 12),
            width=50,
            state='readonly',
            readonlybackground='white'
        )
        password_entry.pack(pady=10, padx=10)
        
        # Password strength indicator
        self.strength_label = tk.Label(
            password_frame,
            text="Strength: Very Strong",
            font=('Arial', 10),
            fg=self.colors['success'],
            bg=self.colors['secondary']
        )
        self.strength_label.pack(pady=5)
        
        # Options frame
        options_frame = tk.LabelFrame(
            main_frame,
            text="Password Options",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        options_frame.pack(fill='x', pady=10)
        
        # Length setting
        length_frame = tk.Frame(options_frame, bg=self.colors['secondary'])
        length_frame.pack(fill='x', pady=5, padx=10)
        
        tk.Label(
            length_frame,
            text="Length:",
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        ).pack(side='left')
        
        self.length_var = tk.IntVar(value=16)
        length_spinbox = tk.Spinbox(
            length_frame,
            from_=8,
            to=128,
            textvariable=self.length_var,
            width=5,
            command=self.generate_password
        )
        length_spinbox.pack(side='right')
        
        # Character type options
        self.uppercase_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Include Uppercase Letters (A-Z)",
            variable=self.uppercase_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success'],
            command=self.generate_password
        ).pack(anchor='w', padx=10, pady=2)
        
        self.lowercase_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Include Lowercase Letters (a-z)",
            variable=self.lowercase_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success'],
            command=self.generate_password
        ).pack(anchor='w', padx=10, pady=2)
        
        self.numbers_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Include Numbers (0-9)",
            variable=self.numbers_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success'],
            command=self.generate_password
        ).pack(anchor='w', padx=10, pady=2)
        
        self.symbols_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Include Symbols (!@#$%^&*)",
            variable=self.symbols_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['success'],
            command=self.generate_password
        ).pack(anchor='w', padx=10, pady=2)
        
        self.ambiguous_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options_frame,
            text="Exclude Ambiguous Characters (0, O, l, 1)",
            variable=self.ambiguous_var,
            font=('Arial', 11),
            fg=self.colors['text_light'],
            bg=self.colors['secondary'],
            selectcolor=self.colors['warning'],
            command=self.generate_password
        ).pack(anchor='w', padx=10, pady=2)
        
        # Preset buttons
        preset_frame = tk.LabelFrame(
            main_frame,
            text="Quick Presets",
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_light'],
            bg=self.colors['secondary']
        )
        preset_frame.pack(fill='x', pady=10)
        
        presets = [
            ("High Security", self.preset_high_security),
            ("Web Safe", self.preset_web_safe),
            ("PIN Code", self.preset_pin),
            ("Passphrase", self.preset_passphrase)
        ]
        
        for i, (text, command) in enumerate(presets):
            if i % 2 == 0:
                preset_row = tk.Frame(preset_frame, bg=self.colors['secondary'])
                preset_row.pack(pady=5)
            
            tk.Button(
                preset_row,
                text=text,
                command=command,
                bg=self.colors['warning'],
                fg='white',
                font=('Arial', 10, 'bold'),
                padx=15,
                pady=5,
                relief=tk.FLAT,
                cursor='hand2'
            ).pack(side='left', padx=5)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        button_frame.pack(fill='x', pady=20)
        
        tk.Button(
            button_frame,
            text="🔄 Generate New",
            command=self.generate_password,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            button_frame,
            text="📋 Copy to Clipboard",
            command=self.copy_to_clipboard,
            bg=self.colors['primary'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            button_frame,
            text="❌ Close",
            command=self.window.destroy,
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side='right', padx=5)
    
    def generate_password(self):
        """Generate password with current settings"""
        try:
            length = self.length_var.get()
            options = {
                'include_uppercase': self.uppercase_var.get(),
                'include_lowercase': self.lowercase_var.get(),
                'include_numbers': self.numbers_var.get(),
                'include_symbols': self.symbols_var.get(),
                'exclude_ambiguous': self.ambiguous_var.get()
            }
            
            password = self.generator.generate_secure_password(length, **options)
            self.password_var.set(password)
            
            # Update strength indicator
            strength_result = self.generator.check_password_strength(password)
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
                text=f"Strength: {strength}",
                fg=color_map.get(strength, self.colors['text_muted'])
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate password:\n{str(e)}")
    
    def copy_to_clipboard(self):
        """Copy generated password to clipboard"""
        password = self.password_var.get()
        if password:
            self.window.clipboard_clear()
            self.window.clipboard_append(password)
            self._clipboard_secret = password
            if self._clipboard_after_id:
                self.window.after_cancel(self._clipboard_after_id)
            timeout = max(1, int(settings.get('security', 'clipboard_clear_timeout', 30)))
            self._clipboard_after_id = self.window.after(timeout * 1000, self._clear_clipboard)
            messagebox.showinfo("Copied", f"Password copied to clipboard for {timeout} seconds.")
        else:
            messagebox.showwarning("Warning", "No password to copy")

    def _clear_clipboard(self):
        try:
            if self.window.clipboard_get() == self._clipboard_secret:
                self.window.clipboard_clear()
        except tk.TclError:
            pass
        self._clipboard_secret = None
    
    def preset_high_security(self):
        """Apply high security preset"""
        self.length_var.set(32)
        self.uppercase_var.set(True)
        self.lowercase_var.set(True)
        self.numbers_var.set(True)
        self.symbols_var.set(True)
        self.ambiguous_var.set(False)
        self.generate_password()
    
    def preset_web_safe(self):
        """Apply web-safe preset"""
        self.length_var.set(16)
        self.uppercase_var.set(True)
        self.lowercase_var.set(True)
        self.numbers_var.set(True)
        self.symbols_var.set(False)
        self.ambiguous_var.set(True)
        self.generate_password()
    
    def preset_pin(self):
        """Apply PIN preset"""
        self.length_var.set(6)
        self.uppercase_var.set(False)
        self.lowercase_var.set(False)
        self.numbers_var.set(True)
        self.symbols_var.set(False)
        self.ambiguous_var.set(True)
        self.generate_password()
    
    def preset_passphrase(self):
        """Apply passphrase preset"""
        try:
            # Generate a passphrase instead
            passphrase = self.generator.generate_passphrase(4)
            self.password_var.set(passphrase)
            
            strength_result = self.generator.check_password_strength(passphrase)
            self.strength_label.config(
                text=f"Strength: {strength_result['strength']}",
                fg=self.colors['success']
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate passphrase:\n{str(e)}")
