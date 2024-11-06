import sqlite3

conn = sqlite3.connect('autoDeploy.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    github_link TEXT NOT NULL,
    subdomain TEXT NOT NULL,
    port TEXT NOT NULL,
    is_deployed BOOLEAN NOT NULL
)
''')
conn.commit()
conn.close()

def add_image(name: str, subdomain: str, github_link: str, port:str, is_deployed: bool) -> None:
    conn = sqlite3.connect('autoDeploy.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT COUNT(*)
    FROM images
    WHERE github_link = ? OR subdomain = ?
    ''', (github_link, subdomain))
    if cursor.fetchone()[0] > 0:
        raise ValueError("This GitHub link or subdomain is already deployed.")
    
    cursor.execute('''
    INSERT INTO images (name, github_link, subdomain, port, is_deployed)
    VALUES (?, ?, ?, ?, ?)
    ''', (name, github_link, subdomain, port, is_deployed))
    
    conn.commit()
    conn.close()
    return True

def toggle_deployment(image_id: int) -> None:
    conn = sqlite3.connect('autoDeploy.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE images
    SET is_deployed = NOT is_deployed
    WHERE id = ?
    ''', (image_id,))
    
    conn.commit()
    conn.close()
    return True

def get_images() -> list:
    conn = sqlite3.connect('autoDeploy.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, name, github_link, subdomain, port, is_deployed
    FROM images
    ''')
    
    images = cursor.fetchall()
    conn.close()
    return images

def get_image(image_id: int) -> tuple:
    conn = sqlite3.connect('autoDeploy.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, name, github_link, subdomain, port, is_deployed
    FROM images
    WHERE id = ?
    ''', (image_id,))
    
    image = cursor.fetchone()
    conn.close()
    return image