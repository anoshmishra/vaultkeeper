-- Add missing columns to user table
ALTER TABLE user ADD COLUMN vault_key TEXT;
ALTER TABLE user ADD COLUMN biometric_enabled INTEGER DEFAULT 0;
ALTER TABLE user ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE user ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP;

-- Check final schema
PRAGMA table_info(user);
