import sqlite3
import os
from werkzeug.security import generate_password_hash

# Assurez-vous que ce chemin est correct par rapport à l'emplacement où vous exécutez le script
DATABASE = 'ciracbot.db'
ADMIN_EMAIL = 'admin@admin.com' # <<< CHANGEZ CECI
ADMIN_USERNAME = 'adminnn' # Ou un autre nom
ADMIN_PASSWORD = 'admin' # <<< CHANGEZ CECI ABSOLUMENT

print("Attempting to create admin user...")

# Vérifier si la base de données existe avant de se connecter
if not os.path.exists(DATABASE):
    print(f"Error: Database file '{DATABASE}' not found.")
    print("Please run 'flask init-db' first.")
    exit() # Quitter si la DB n'existe pas

conn = None
try:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Vérifier si l'admin existe déjà
    cursor.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,))
    existing_admin = cursor.fetchone()

    if existing_admin:
        print(f"Admin user with email {ADMIN_EMAIL} already exists (ID: {existing_admin[0]}).")
    else:
        # Vérifier si la table users existe (au cas où init-db n'aurait pas fonctionné correctement)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
             print(f"Error: Table 'users' not found in database '{DATABASE}'.")
             print("Please ensure 'flask init-db' completed successfully.")
             exit()

        # Créer le hash du mot de passe
        password_hash = generate_password_hash(ADMIN_PASSWORD)

        # Insérer l'utilisateur admin
        cursor.execute(
            'INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)',
            (ADMIN_EMAIL, ADMIN_USERNAME, password_hash, 'admin')
        )
        conn.commit()
        print(f"Admin user '{ADMIN_EMAIL}' created successfully!")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    if conn:
        conn.rollback() # Annuler les changements en cas d'erreur
except Exception as e:
     print(f"An unexpected error occurred: {e}")
finally:
    if conn:
        conn.close()
        # print("Database connection closed.") # Optionnel

print("Script finished.")