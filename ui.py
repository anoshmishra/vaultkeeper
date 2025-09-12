# ui.py
import tkinter as tk
from tkinter import simpledialog, messagebox
import database
import encryption

class VaultKeeperApp:
    def __init__(self, master):
        self.master = master
        self.master.title("VaultKeeper")
        database.init_db()
        self.init_screen()

    def init_screen(self):
        user = database.get_user()
        if not user:
            self.create_master_password_screen()
        else:
            self.login_screen(user)

    def create_master_password_screen(self):
        def submit():
            pw = entry.get()
            if len(pw) < 6:
                messagebox.showwarning("Weak Password", "Choose a longer master password!")
                return
            salt = encryption.generate_salt()
            master_hash = encryption.hash_master_password(pw)
            database.save_master_password(master_hash, salt)
            messagebox.showinfo("Success", "Master password set. Please log in.")
            self.clear()
            self.init_screen()

        self.clear()
        tk.Label(self.master, text="Set Master Password:").pack(pady=10)
        entry = tk.Entry(self.master, show="*")
        entry.pack()
        tk.Button(self.master, text="Set", command=submit).pack(pady=10)

    def login_screen(self, user):
        master_hash, salt = user

        def submit():
            pw = entry.get()
            if not encryption.verify_master_password(master_hash, pw):
                messagebox.showerror("Error", "Wrong password!")
                return
            self.session_key = encryption.derive_key(pw, salt)
            self.clear()
            self.vault_screen()

        self.clear()
        tk.Label(self.master, text="Enter Master Password:").pack(pady=10)
        entry = tk.Entry(self.master, show="*")
        entry.pack()
        tk.Button(self.master, text="Login", command=submit).pack(pady=10)

    def vault_screen(self):
        self.clear()
        tk.Label(self.master, text="Your Credentials:").pack()
        creds = database.get_credentials()
        for cred in creds:
            cred_id, site, username, enc_pass, notes = cred
            try:
                password = encryption.decrypt_password(enc_pass, self.session_key)
            except Exception:
                password = "***error***"
            tk.Label(self.master, text=f"{site} | {username} | {password}").pack()

        tk.Button(self.master, text="Add", command=self.add_credential_screen).pack(pady=10)

    def add_credential_screen(self):
        self.clear()
        tk.Label(self.master, text="Add Credential").pack()
        fields = ["Site", "Username", "Password", "Notes"]
        entries = {}
        for field in fields:
            tk.Label(self.master, text=field).pack()
            entries[field] = tk.Entry(self.master, show="*" if field == "Password" else None)
            entries[field].pack()

        def submit():
            encrypted_pass = encryption.encrypt_password(entries["Password"].get(), self.session_key)
            database.add_credential(
                entries["Site"].get(), entries["Username"].get(), encrypted_pass, entries["Notes"].get())
            self.vault_screen()

        tk.Button(self.master, text="Save", command=submit).pack(pady=10)

    def clear(self):
        for widget in self.master.winfo_children():
            widget.destroy()
