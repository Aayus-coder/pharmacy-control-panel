def setup_database():
    conn = sqlite3.connect('pharma_chain.db')
    cursor = conn.cursor()
    
    # Create tables with proper schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blocks (
        block_index INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        data_hash TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        payload TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medicines (
        medicine_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        potency TEXT,
        brand TEXT CHECK(brand IN ('SBL', 'Bakson', 'Reckeweg', 'Wheezal', 'Allen')),
        form TEXT CHECK(form IN ('Drops', 'Tablets', 'Ointment', 'Injection')),
        qty INTEGER,
        price REAL,
        expiry DATE,
        batch_number TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        block_hash TEXT,
        FOREIGN KEY (block_hash) REFERENCES blocks(data_hash)
    )''')
    
    # Initialize with sample data only if tables are empty
    cursor.execute("SELECT COUNT(*) FROM medicines")
    if cursor.fetchone()[0] == 0:
        sample_medicines = [
            ('Arnica Montana', '30C', 'SBL', 'Tablets', 50, 120.0, '2025-12-31', 'ARN30C-2025'),
            ('Nux Vomica', '200C', 'SBL', 'Drops', 30, 150.0, '2024-11-15', 'NUX200-2024')
        ]
        
        # Create genesis block first
        cursor.execute('''
        INSERT INTO blocks (data_hash, previous_hash, payload)
        VALUES (?, ?, ?)
        ''', ('0'*64, '0'*64, 'Genesis Block'))
        
        # Insert medicines
        for med in sample_medicines:
            block_data = str(med)
            current_hash = hashlib.sha256(block_data.encode()).hexdigest()
            
            cursor.execute('''
            INSERT INTO medicines 
            (name, potency, brand, form, qty, price, expiry, batch_number, block_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*med, current_hash))
            
            cursor.execute('''
            INSERT INTO blocks (data_hash, previous_hash, payload)
            VALUES (?, ?, ?)
            ''', (current_hash, '0'*64, f"Added {med[0]}"))
    
    conn.commit()
    return conn