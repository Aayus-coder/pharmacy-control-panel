import sqlite3
import hashlib
from datetime import datetime

def setup_database():
    """Initialize the database with blockchain-integrated tables and sample data"""
    try:
        conn = sqlite3.connect('pharma_chain.db')
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create blockchain table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            block_index INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_hash TEXT NOT NULL UNIQUE,
            previous_hash TEXT NOT NULL,
            payload TEXT,
            nonce INTEGER DEFAULT 0
        )''')

        # Create medicines table with constraints
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            medicine_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            potency TEXT,
            brand TEXT CHECK(brand IN ('SBL', 'Bakson', 'Reckeweg', 'Wheezal', 'Allen')),
            form TEXT CHECK(form IN ('Drops', 'Tablets', 'Ointment', 'Injection')),
            qty INTEGER CHECK(qty >= 0),
            price REAL CHECK(price > 0),
            expiry DATE CHECK(expiry > CURRENT_DATE),
            batch_number TEXT UNIQUE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            block_hash TEXT NOT NULL,
            FOREIGN KEY (block_hash) REFERENCES blocks(data_hash) ON DELETE RESTRICT
        )''')
        
        # Initialize with sample data if empty
        cursor.execute("SELECT COUNT(*) FROM medicines")
        if cursor.fetchone()[0] == 0:
            # Create genesis block
            genesis_hash = hashlib.sha256(b'genesis').hexdigest()
            cursor.execute('''
            INSERT INTO blocks (data_hash, previous_hash, payload, nonce)
            VALUES (?, ?, ?, ?)
            ''', (genesis_hash, '0'*64, 'Genesis Block', 0))
            
            # Sample medicines with realistic data
            sample_medicines = [
                ('Arnica Montana', '30C', 'SBL', 'Tablets', 50, 120.0, '2025-12-31', 'ARN30C-2025'),
                ('Nux Vomica', '200C', 'SBL', 'Drops', 30, 150.0, '2024-11-15', 'NUX200-2024'),
                ('Belladonna', '1M', 'Bakson', 'Tablets', 25, 95.0, '2026-03-31', 'BELL1M-2026')
            ]
            
            # Insert sample medicines with blockchain linkage
            for med in sample_medicines:
                med_data = {
                    'name': med[0],
                    'details': med[1:-1],  # Exclude batch number from hash
                    'timestamp': str(datetime.now())
                }
                current_hash = calculate_hash(med_data)
                
                cursor.execute('''
                INSERT INTO medicines 
                (name, potency, brand, form, qty, price, expiry, batch_number, block_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (*med, current_hash))
                
                cursor.execute('''
                INSERT INTO blocks (data_hash, previous_hash, payload)
                VALUES (?, ?, ?)
                ''', (current_hash, genesis_hash, f"Added {med[0]} ({med[7]})"))
        
        conn.commit()
        print("Database initialized successfully")
        return conn
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

def calculate_hash(data):
    """Calculate SHA-256 hash of structured data"""
    if isinstance(data, dict):
        data = str(sorted(data.items())).encode()
    return hashlib.sha256(data).hexdigest()

def verify_medicine(conn, batch_number):
    """Verify medicine integrity against blockchain"""
    try:
        cursor = conn.cursor()
        
        # Get medicine and its block
        cursor.execute('''
        SELECT m.*, b.timestamp, b.previous_hash 
        FROM medicines m
        JOIN blocks b ON m.block_hash = b.data_hash
        WHERE m.batch_number = ?
        ''', (batch_number,))
        
        medicine = cursor.fetchone()
        if not medicine:
            return False, "Medicine not found"
            
        # Verify hash chain
        current_hash = medicine[-1]  # block_hash
        while current_hash != '0'*64:  # Until genesis block
            cursor.execute('''
            SELECT data_hash, previous_hash, payload 
            FROM blocks 
            WHERE data_hash = ?
            ''', (current_hash,))
            
            block = cursor.fetchone()
            if not block:
                return False, "Blockchain integrity compromised"
                
            current_hash = block[1]  # previous_hash
            
        return True, "Verification successful"
        
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
