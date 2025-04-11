import sqlite3
import os
from werkzeug.security import generate_password_hash

# --- Configuration ---
DATABASE = 'ciracbot.db' # Assurez-vous que c'est le bon nom de fichier DB

# --- DÉFINISSEZ ICI LES INFOS DU NOUVEL UTILISATEUR ---
NEW_USER_EMAIL = 'user@user.com' # <<< CHANGEZ CET EMAIL (doit être unique)
NEW_USER_USERNAME = 'Test User'         # <<< CHANGEZ CE NOM UTILISATEUR
NEW_USER_PASSWORD = 'user123'       # <<< CHANGEZ CE MOT DE PASSE (pour un plus sûr)
NEW_USER_ROLE = 'user'                  # Rôle spécifique pour cet utilisateur

print(f"Attempting to create user with email: {NEW_USER_EMAIL} and role: {NEW_USER_ROLE}")

# Vérifier si la base de données existe
if not os.path.exists(DATABASE):
    print(f"Error: Database file '{DATABASE}' not found.")
    print("Please run 'flask init-db' first.")
    exit()

conn = None
try:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Vérifier si l'email existe déjà
    cursor.execute("SELECT id FROM users WHERE email = ?", (NEW_USER_EMAIL,))
    existing_user = cursor.fetchone()

    if existing_user:
        print(f"Error: User with email {NEW_USER_EMAIL} already exists (ID: {existing_user[0]}).")
    else:
        # Vérifier si la table users existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
             print(f"Error: Table 'users' not found in database '{DATABASE}'.")
             print("Please ensure 'flask init-db' completed successfully.")
             exit()

        # Hacher le mot de passe
        password_hash = generate_password_hash(NEW_USER_PASSWORD)

        # Insérer le nouvel utilisateur avec le rôle 'user'
        cursor.execute(
            'INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)',
            (NEW_USER_EMAIL, NEW_USER_USERNAME, password_hash, NEW_USER_ROLE) # Utilise NEW_USER_ROLE
        )
        conn.commit()
        print(f"User '{NEW_USER_EMAIL}' (Role: {NEW_USER_ROLE}) created successfully!")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    if conn:
        conn.rollback()
except Exception as e:
     print(f"An unexpected error occurred: {e}")
finally:
    if conn:
        conn.close()

print("Script finished.")