# advanced/universal_storage.py
import json
import os
import mimetypes
from datetime import datetime
from pathlib import Path
import sqlite3

from advanced.encryption_advanced import ZeroKnowledgeEncryption

class UniversalDataManager:
    def __init__(self, encryption_key):
        self.encryption_key = encryption_key
        self.encryption = ZeroKnowledgeEncryption()
        self.db_path = str(Path(__file__).resolve().parent.parent / "vaultkeeper_universal.db")
        self.init_universal_db()
    
    def init_universal_db(self):
        """Initialize database for universal data storage"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS universal_storage (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                data_type TEXT NOT NULL,
                encrypted_data BLOB NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_data(self, name, data, category="general", tags=None, metadata=None):
        """Store any type of data with encryption"""
        
        # Determine data type and serialize
        if isinstance(data, dict):
            data_type = "json"
            serialized_data = json.dumps(data).encode()
        elif isinstance(data, str):
            data_type = "text"
            serialized_data = data.encode()
        elif isinstance(data, (list, tuple)):
            data_type = "list"
            serialized_data = json.dumps(data).encode()
        elif isinstance(data, bytes):
            data_type = "binary"
            serialized_data = data
        else:
            raise TypeError("Only text, bytes, lists, and dictionaries can be stored securely")
        
        # Encrypt the data
        encrypted_data = self.encryption.encrypt_data(serialized_data, self.encryption_key)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO universal_storage 
            (name, category, data_type, encrypted_data, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, data_type, encrypted_data, 
              json.dumps(tags) if tags else None,
              json.dumps(metadata) if metadata else None))
        
        item_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
    
    def retrieve_data(self, name=None, item_id=None, category=None):
        """Retrieve and decrypt stored data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if item_id:
            c.execute("SELECT * FROM universal_storage WHERE id = ?", (item_id,))
        elif name and category:
            c.execute("SELECT * FROM universal_storage WHERE name = ? AND category = ?", 
                     (name, category))
        elif name:
            c.execute("SELECT * FROM universal_storage WHERE name = ?", (name,))
        else:
            return None, "Must provide either item_id or name"
        
        result = c.fetchone()
        
        if not result:
            conn.close()
            return None, "Data not found"
        
        item_id, name, category, data_type, encrypted_data, tags, created_at, updated_at, accessed_at, metadata = result
        
        # Update access time
        c.execute("UPDATE universal_storage SET accessed_at = CURRENT_TIMESTAMP WHERE id = ?", 
                 (item_id,))
        conn.commit()
        conn.close()
        
        try:
            # Decrypt the data
            decrypted_data = self.encryption.decrypt_data(encrypted_data, self.encryption_key)
            
            # Deserialize based on data type
            if data_type == "json":
                data = json.loads(decrypted_data.decode())
            elif data_type == "text":
                data = decrypted_data.decode()
            elif data_type == "list":
                data = json.loads(decrypted_data.decode())
            elif data_type == "binary":
                data = decrypted_data
            else:
                data = decrypted_data
            
            return {
                'id': item_id,
                'name': name,
                'category': category,
                'data': data,
                'data_type': data_type,
                'tags': json.loads(tags) if tags else None,
                'metadata': json.loads(metadata) if metadata else None,
                'created_at': created_at,
                'updated_at': updated_at,
                'accessed_at': accessed_at
            }, "Success"
            
        except Exception as e:
            return None, f"Decryption failed: {str(e)}"
    
    def list_all_data(self, category=None):
        """List all stored data items"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if category:
            c.execute("""
                SELECT id, name, category, data_type, tags, created_at, updated_at, accessed_at, metadata
                FROM universal_storage WHERE category = ?
                ORDER BY updated_at DESC
            """, (category,))
        else:
            c.execute("""
                SELECT id, name, category, data_type, tags, created_at, updated_at, accessed_at, metadata
                FROM universal_storage
                ORDER BY category ASC, updated_at DESC
            """)
        
        items = c.fetchall()
        conn.close()
        
        return [
            {
                'id': item[0],
                'name': item[1],
                'category': item[2],
                'data_type': item[3],
                'tags': json.loads(item[4]) if item[4] else None,
                'created_at': item[5],
                'updated_at': item[6],
                'accessed_at': item[7],
                'metadata': json.loads(item[8]) if item[8] else None
            }
            for item in items
        ]
    
    def store_file(self, file_path, name=None, category="files", tags=None, metadata=None):
        """Store any file (image, video, document) with encryption"""
        
        file_path = Path(file_path)
        if not file_path.exists():
            return None, "File not found"
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Get file info
            file_size = len(file_data)
            file_extension = file_path.suffix.lower()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Use filename if no name provided
            if not name:
                name = file_path.name
            
            # Create metadata
            file_metadata = {
                'original_filename': file_path.name,
                'file_size': file_size,
                'file_extension': file_extension,
                'mime_type': mime_type or 'application/octet-stream',
                'upload_date': datetime.now().isoformat()
            }
            
            # Add custom metadata if provided
            if metadata:
                file_metadata.update(metadata)
            
            # Store encrypted file
            item_id = self.store_data(
                name=name,
                data=file_data,  # Binary data
                category=category,
                tags=tags,
                metadata=file_metadata
            )
            
            return item_id, f"File '{name}' stored successfully ({file_size} bytes)"
            
        except Exception as e:
            return None, f"Failed to store file: {str(e)}"
    
    def retrieve_file(self, item_id, output_path=None):
        """Retrieve and optionally save file to disk"""
        
        result, status = self.retrieve_data(item_id=item_id)
        
        if not result:
            return None, status
        
        file_data = result['data']
        metadata = result['metadata']
        
        if output_path:
            try:
                # Save file to specified path
                with open(output_path, 'wb') as f:
                    f.write(file_data)
                
                return {
                    'file_path': output_path,
                    'metadata': metadata,
                    'size': len(file_data)
                }, "File retrieved and saved successfully"
                
            except Exception as e:
                return None, f"Failed to save file: {str(e)}"
        else:
            # Return file data in memory
            return {
                'data': file_data,
                'metadata': metadata,
                'size': len(file_data)
            }, "File retrieved successfully"
    
    def update_data(self, item_id, new_data=None, new_name=None, new_category=None, 
                   new_tags=None, new_metadata=None):
        """Update existing data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        updates = []
        params = []
        
        if new_data is not None:
            # Serialize and encrypt new data
            if isinstance(new_data, dict):
                data_type = "json"
                serialized_data = json.dumps(new_data).encode()
            elif isinstance(new_data, str):
                data_type = "text"
                serialized_data = new_data.encode()
            elif isinstance(new_data, (list, tuple)):
                data_type = "list"
                serialized_data = json.dumps(new_data).encode()
            elif isinstance(new_data, bytes):
                data_type = "binary"
                serialized_data = new_data
            else:
                raise TypeError("Only text, bytes, lists, and dictionaries can be stored securely")
            
            encrypted_data = self.encryption.encrypt_data(serialized_data, self.encryption_key)
            updates.extend(["encrypted_data = ?", "data_type = ?"])
            params.extend([encrypted_data, data_type])
        
        if new_name:
            updates.append("name = ?")
            params.append(new_name)
        
        if new_category:
            updates.append("category = ?")
            params.append(new_category)
        
        if new_tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(new_tags) if new_tags else None)
        
        if new_metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(new_metadata) if new_metadata else None)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(item_id)
            
            query = f"UPDATE universal_storage SET {', '.join(updates)} WHERE id = ?"
            c.execute(query, params)
            conn.commit()
            success = c.rowcount > 0
        else:
            success = False
        
        conn.close()
        return success
    
    def delete_data(self, item_id):
        """Delete stored data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM universal_storage WHERE id = ?", (item_id,))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def search_data(self, search_term, search_in=['name', 'category', 'tags']):
        """Search for data by name, category, or tags"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        conditions = []
        params = []
        
        if 'name' in search_in:
            conditions.append("name LIKE ?")
            params.append(f"%{search_term}%")
        
        if 'category' in search_in:
            conditions.append("category LIKE ?")
            params.append(f"%{search_term}%")
        
        if 'tags' in search_in:
            conditions.append("tags LIKE ?")
            params.append(f"%{search_term}%")
        
        if not conditions:
            return []
        
        query = f"""
            SELECT id, name, category, data_type, tags, created_at, updated_at
            FROM universal_storage
            WHERE {' OR '.join(conditions)}
            ORDER BY updated_at DESC
        """
        
        c.execute(query, params)
        items = c.fetchall()
        conn.close()
        
        return [
            {
                'id': item[0],
                'name': item[1],
                'category': item[2],
                'data_type': item[3],
                'tags': json.loads(item[4]) if item[4] else None,
                'created_at': item[5],
                'updated_at': item[6]
            }
            for item in items
        ]
    
    def get_files_by_type(self, file_type=None):
        """Get files filtered by type (images, videos, documents)"""
        
        all_items = self.list_all_data(category="files")
        
        if not file_type:
            return all_items
        
        type_mappings = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }
        
        if file_type not in type_mappings:
            return []
        
        extensions = type_mappings[file_type]
        filtered_items = []
        
        for item in all_items:
            metadata = item.get('metadata', {})
            if isinstance(metadata, dict):
                file_ext = metadata.get('file_extension', '').lower()
                if file_ext in extensions:
                    filtered_items.append(item)
        
        return filtered_items

    def store_api_key(self, name, secret, tags=None, metadata=None):
        """Store an API token in the same encrypted vault as files and notes."""
        return self.store_data(name, secret, category="api_keys", tags=tags, metadata=metadata)

    def store_ssh_key(self, name, private_key, public_key=None, tags=None):
        """Store an SSH private key without exposing it in SQLite metadata."""
        payload = {"private_key": private_key, "public_key": public_key}
        return self.store_data(name, payload, category="ssh_keys", tags=tags, metadata={"key_type": "ssh"})
