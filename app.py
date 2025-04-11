import dash
from dash import dcc, html, Input, Output, State, callback 
import dash_bootstrap_components as dbc
import json
import os
import flask 
import re
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user 
from werkzeug.security import generate_password_hash, check_password_hash 
import sqlite3 
import click 
from flask.cli import with_appcontext 


from components import navbar


server = flask.Flask(__name__)


PREFERENCES_FILE = "preferences.json"
try:
    with open(PREFERENCES_FILE, "r") as f:
        preferences = json.load(f)
        theme_preference = preferences.get("theme", "light")
except (FileNotFoundError, json.JSONDecodeError):
    theme_preference = "light"

server.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(24)),
)

# --- Configuration Base de Données SQLite ---
DATABASE = 'ciracbot.db'

def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@server.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    try:
        print("Attempting to create users table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user', 'admin'))
            );
        ''')
        db.commit()
        print("Table 'users' checked/created successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred during DB initialization: {e}")

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

server.cli.add_command(init_db_command)

# --- Fonctions d'accès aux données utilisateur ---
def find_user_by_email(email):
    db = get_db()
    try:
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        return user
    except sqlite3.Error as e:
        print(f"Database error in find_user_by_email: {e}")
        return None

def find_user_by_id(user_id):
    db = get_db()
    try:
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return user
    except sqlite3.Error as e:
        print(f"Database error in find_user_by_id: {e}")
        return None

# --- Classe Utilisateur pour Flask-Login ---
class User(UserMixin):
    def __init__(self, user_id, email, role, username):
        self.id = user_id
        self.email = email
        self.role = role
        self.username = username

# --- Configuration Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login" # Chemin relatif vers la page de login

@login_manager.user_loader
def load_user(user_id):
    user_data = find_user_by_id(user_id)
    if user_data:
        return User(user_id=user_data['id'], email=user_data['email'], role=user_data['role'], username=user_data['username'])
    return None

# --- Initialisation de Dash ---
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True, # <-- ACTIVER DASH PAGES
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True # Garder si nécessaire
)
app.title = "CIRACbot"

# --- Routes Flask pour l'Authentification ---
@server.route('/login', methods=['POST'])
def login_post():
    print("\n--- LOGIN POST START ---") # Marqueur de début clair

    # Chemin 1: Vérifier si l'utilisateur est déjà authentifié
    if current_user.is_authenticated:
        print("User already authenticated, redirecting home.")
        try:
            # Essayer d'obtenir le chemin de la page d'accueil depuis le registre
            home_path = dash.page_registry['pages.accueil']['relative_path']
            print(f"Redirecting to (already auth): {home_path}")
            print("--- LOGIN POST END (Already Auth) ---\n")
            return flask.redirect(home_path)
        except KeyError:
            # Fallback si la page d'accueil n'est pas trouvée dans le registre
            print("WARNING: 'pages.accueil' not found in page_registry. Redirecting to '/'.")
            print("--- LOGIN POST END (Already Auth - Fallback) ---\n")
            return flask.redirect('/')

    # Récupérer les données du formulaire
    email = flask.request.form.get('email')
    password = flask.request.form.get('password')
    print(f"Received data - Email: '{email}', Password provided: {'Yes' if password else 'No'}")

    # Vérifier si email et password ont été fournis
    if not email or not password:
        print("Login FAILED: Email or Password not provided in form.")
        flask.flash('Adresse e-mail et mot de passe requis.', 'error')
        try:
            login_path = dash.page_registry['pages.login']['relative_path']
            print(f"Redirecting back to login (missing data): {login_path}")
            print("--- LOGIN POST END (Missing Data) ---\n")
            return flask.redirect(login_path)
        except KeyError:
            print("WARNING: 'pages.login' not found in page_registry. Redirecting to '/login'.")
            print("--- LOGIN POST END (Missing Data - Fallback) ---\n")
            return flask.redirect('/login')


    # Rechercher l'utilisateur dans la base de données
    print(f"Searching database for email: '{email}'")
    user_data = find_user_by_email(email)
    # Afficher le résultat (None ou les données de l'utilisateur sans le hash!)
    if user_data:
         # Convertir Row en dict pour affichage sûr (sans le hash)
         user_data_display = {key: user_data[key] for key in user_data.keys() if key != 'password_hash'}
         print(f"Database result: User FOUND - {user_data_display}")
    else:
         print(f"Database result: User with email '{email}' NOT FOUND.")


    # Chemin 2: Essayer de valider si l'utilisateur a été trouvé
    if user_data:
        # Comparer le mot de passe fourni avec le hash stocké
        print("Comparing provided password with stored hash...")
        password_match = check_password_hash(user_data['password_hash'], password)
        print(f"Password check result: {password_match}") # True ou False

        if password_match:
            # Chemin 2a: Connexion réussie
            user_obj = User(user_id=user_data['id'], email=user_data['email'], role=user_data['role'], username=user_data['username'])
            login_user(user_obj) # Connecter l'utilisateur
            print(f"Login SUCCESS for '{email}'. Role: '{user_obj.role}'. User session established.")

            # Gérer la redirection après succès
            next_page = flask.request.args.get('next')
            print(f"Optional 'next' parameter from URL: {next_page}")
            try:
                home_path = dash.page_registry['pages.accueil']['relative_path']
                # Utiliser 'next' s'il existe et est sûr (simplifié ici), sinon l'accueil
                target_url = next_page or home_path
                print(f"Redirecting to (success): {target_url}")
                print("--- LOGIN POST END (Success) ---\n")
                return flask.redirect(target_url)
            except KeyError:
                print("WARNING: 'pages.accueil' not found in page_registry. Redirecting to '/'.")
                print("--- LOGIN POST END (Success - Fallback) ---\n")
                return flask.redirect('/')
        else:
            # Chemin 2b: Mauvais mot de passe
            print(f"Login FAILED for '{email}': Incorrect password.")
            flask.flash('Adresse e-mail ou mot de passe incorrect.', 'error')
            # Rediriger vers la page de login pour afficher l'erreur flash
            try:
                login_path = dash.page_registry['pages.login']['relative_path']
                print(f"Redirecting back to login (incorrect password): {login_path}")
                print("--- LOGIN POST END (Incorrect Password) ---\n")
                return flask.redirect(login_path)
            except KeyError:
                 print("WARNING: 'pages.login' not found in page_registry. Redirecting to '/login'.")
                 print("--- LOGIN POST END (Incorrect Password - Fallback) ---\n")
                 return flask.redirect('/login')

    # Chemin 3: Utilisateur non trouvé dans la base de données
    else:
        print(f"Login FAILED: User with email '{email}' not found in database.")
        flask.flash('Adresse e-mail ou mot de passe incorrect.', 'error') # Message générique
        # Rediriger vers la page de login pour afficher l'erreur flash
        try:
            login_path = dash.page_registry['pages.login']['relative_path']
            print(f"Redirecting back to login (user not found): {login_path}")
            print("--- LOGIN POST END (User Not Found) ---\n")
            return flask.redirect(login_path)
        except KeyError:
             print("WARNING: 'pages.login' not found in page_registry. Redirecting to '/login'.")
             print("--- LOGIN POST END (User Not Found - Fallback) ---\n")
             return flask.redirect('/login')

    # Note: Théoriquement, on ne devrait jamais atteindre ce point car tous les cas mènent à un return.
    # Mais par sécurité, on peut ajouter un fallback final.
    print("ERROR: Reached unexpected end of login_post function.")
    print("--- LOGIN POST END (Unexpected Fallthrough) ---\n")
    return flask.redirect('/login') # Fallback général
@server.route('/logout')
def logout():
    logout_user()
    login_path = dash.page_registry['pages.login']['relative_path']
    return flask.redirect(login_path)

@server.route('/register', methods=['POST'])
def register_post():
    print("\n--- REGISTER POST START ---")
    # 1. Récupérer les données du formulaire
    first_name = flask.request.form.get('first_name')
    last_name = flask.request.form.get('last_name')
    email = flask.request.form.get('email')
    age = flask.request.form.get('age') # Sera une chaîne
    password = flask.request.form.get('password')
    confirm_password = flask.request.form.get('confirm_password')
    username = f"{first_name} {last_name}" if first_name and last_name else email # Créer un username

    print(f"Registration attempt for: {email}")

    # 2. Valider les données (TRÈS IMPORTANT)
    error_messages = []
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not first_name or not first_name.strip(): error_messages.append("Prénom requis.")
    if not last_name or not last_name.strip(): error_messages.append("Nom requis.")
    if not email or not email.strip():
        error_messages.append("Email requis.")
    elif not re.match(email_regex, email.strip()):
        error_messages.append("Format d'email invalide.")
    # Ajouter validation pour l'âge si nécessaire
    # Exemple: if age and not age.isdigit(): error_messages.append("L'âge doit être un nombre.")

    if not password: error_messages.append("Mot de passe requis.")
    elif len(password) < 6: error_messages.append("Le mot de passe doit faire au moins 6 caractères.")
    elif password != confirm_password: error_messages.append("Les mots de passe ne correspondent pas.")

    # Vérifier si l'email existe déjà dans la DB (seulement si pas déjà d'autres erreurs)
    # Et si l'email est valide
    if not error_messages and email and re.match(email_regex, email.strip()):
        if find_user_by_email(email.strip()): # Utilise la fonction existante
             error_messages.append("Cette adresse e-mail est déjà utilisée.")

    # 3. Si erreurs, retourner à la page avec message(s) flash
    if error_messages:
        for msg in error_messages:
            # Utiliser une catégorie pour pouvoir cibler le bon Div avec le callback flash
            flask.flash(msg, 'register-error')
        print(f"Registration FAILED for {email}: {error_messages}")
        print("--- REGISTER POST END (Validation Fail) ---\n")
        # Rediriger vers la page de login pour voir les messages
        # (Il faudrait idéalement aussi passer l'onglet 'register' comme actif)
        try:
            login_path = dash.page_registry['pages.login']['relative_path']
            # Optionnel: ajouter un ?tab=register à l'URL pour essayer d'ouvrir le bon onglet
            # return flask.redirect(f"{login_path}?tab=register")
            return flask.redirect(login_path)
        except KeyError:
             return flask.redirect('/login')


    # 4. Si valide, créer l'utilisateur
    try:
        print(f"Data validation passed for {email}. Attempting to create user.")
        password_hash = generate_password_hash(password)
        # Assurez-vous que cette fonction existe et gère bien les erreurs
        new_user_id = create_user_in_db(email.strip(), username, password_hash, role='user', age=age)

        if new_user_id:
             print(f"Registration SUCCESS for {email}. New user ID: {new_user_id}")
             # Message de succès avec une catégorie différente
             flask.flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", 'register-success')
             print("--- REGISTER POST END (Success) ---\n")
             try:
                 login_path = dash.page_registry['pages.login']['relative_path']
                 return flask.redirect(login_path) # Rediriger vers login après succès
             except KeyError:
                 return flask.redirect('/login')
        else:
             # Erreur lors de la création en DB (ex: email déjà pris malgré la vérif, ou autre)
             print(f"Registration FAILED for {email}: Database insertion error (maybe email constraint?).")
             flask.flash("Erreur lors de la création du compte (l'email est peut-être déjà pris). Veuillez réessayer.", 'register-error')
             print("--- REGISTER POST END (DB Error) ---\n")
             try:
                 login_path = dash.page_registry['pages.login']['relative_path']
                 return flask.redirect(login_path)
             except KeyError:
                 return flask.redirect('/login')

    except Exception as e:
        print(f"EXCEPTION during registration processing for {email}: {e}") # Log l'erreur serveur
        flask.flash("Une erreur serveur inattendue s'est produite.", 'register-error')
        print("--- REGISTER POST END (Exception) ---\n")
        try:
            login_path = dash.page_registry['pages.login']['relative_path']
            return flask.redirect(login_path)
        except KeyError:
            return flask.redirect('/login')
# --- FIN DE LA NOUVELLE ROUTE ---

def create_user_in_db(email, username, password_hash, role='user', age=None):
    """Insère un nouvel utilisateur dans la DB. Retourne l'ID ou None."""
    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)',
            (email, username, password_hash, role)
        )
        db.commit()
        print(f"DB: User {email} inserted with ID: {cursor.lastrowid}")
        return cursor.lastrowid
    except sqlite3.IntegrityError: # Email déjà pris (contrainte UNIQUE)
        print(f"DB ERROR: Email {email} already exists (IntegrityError).")
        db.rollback() # Annuler la transaction
        return None
    except sqlite3.Error as e: # Autre erreur SQLite
        print(f"DB ERROR in create_user_in_db for {email}: {e}")
        db.rollback()
        return None

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=True), # refresh peut être utile
        dcc.Store(id='theme-store', data=theme_preference),
        # Le conteneur global pour appliquer le thème
        html.Div(id='app-container', children=[
            # La navbar sera mise à jour par son propre callback ou dynamiquement
            html.Div(id='navbar-container'), # Conteneur pour la navbar dynamique

            # dash.page_container affichera le contenu de la page actuelle
            # trouvée dans le dossier 'pages' par Dash
            dbc.Container(dash.page_container, fluid=True, className="pt-4")
        ])
    ]
)


@callback(
    Output('navbar-container', 'children'),
    Input('url', 'pathname') # Se déclenche au changement d'URL (pour refléter login/logout)
)
def update_navbar(_pathname):
    # Assurez-vous que votre fonction navbar.Navbar accepte current_user
    # et adapte les liens affichés (Se connecter/Déconnexion, Agent, etc.)
    return navbar.Navbar(current_user)

# Callback pour afficher les messages Flash (sur la page de login)
@callback(
    # L'ID de sortie DOIT correspondre à un élément dans pages/login.py
    Output('login-flash-output', 'children', allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def display_flash_messages_login(pathname):
    # Assurez-vous que la page /login est enregistrée correctement
    login_path = dash.page_registry.get('pages.login', {}).get('relative_path', '/login-fallback')
    if pathname == login_path:
        flashed_messages = flask.get_flashed_messages(with_categories=True)
        if flashed_messages:
            return html.Div([
                # Utiliser des alertes Bootstrap pour un meilleur style
                dbc.Alert(message, color=category if category in ['danger', 'warning', 'success', 'info'] else 'info', dismissable=True)
                for category, message in flashed_messages
            ], className="mt-3") # Ajouter une marge
    return ""

# Callback pour changer le thème appliqué au conteneur (INCHANGÉ)
@callback(
    Output('app-container', 'className'),
    Input('theme-store', 'data')
)
def update_theme_class(theme_value):
    print(f"APP.PY Callback: Received from theme-store: {theme_value}")
    if theme_value == 'dark':
        print(f"APP.PY Callback: Applying className: theme-dark")
        return 'theme-dark'
    else:
        print(f"APP.PY Callback: Applying className: theme-light")
        return 'theme-light'

# Callback pour le Toggler de la Navbar (si vous avez un menu burger)
@callback(
    Output("navbar-collapse", "is_open", allow_duplicate=True), # ID doit exister dans navbar.py
    [Input("navbar-toggler", "n_clicks")], # ID doit exister dans navbar.py
    [State("navbar-collapse", "is_open")],
    prevent_initial_call=True
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    Output('register-feedback-output', 'children', allow_duplicate=True), # Cible la Div dans login.py (onglet inscription)
    Input('url', 'pathname'), # Se déclenche quand on arrive sur la page (après redirection)
    prevent_initial_call=True
)
def display_flash_messages_register(pathname):
    # Vérifier si on est sur la page où afficher (généralement /login après la redirection)
    try:
        login_path = dash.page_registry['pages.login']['relative_path']
    except KeyError:
        login_path = '/login' # Fallback

    if pathname == login_path:
        # Récupérer les messages flash avec les catégories spécifiques
        success_messages = flask.get_flashed_messages(category_filter=["register-success"])
        error_messages = flask.get_flashed_messages(category_filter=["register-error"])

        alerts = []
        if success_messages:
            for msg in success_messages:
                alerts.append(dbc.Alert(msg, color="success", dismissable=True, duration=6000)) # Auto-fermeture après 6s
        if error_messages:
             for msg in error_messages:
                alerts.append(dbc.Alert(msg, color="danger", dismissable=True)) # Reste affiché

        if alerts:
            return html.Div(alerts)
    # Si pas sur la bonne page ou pas de message, ne rien faire
    return no_update


# --- Lancement de l'Application ---
if __name__ == '__main__':
    # Initialiser la DB si nécessaire (mieux via 'flask init-db' en terminal)
    # with server.app_context():
    #    init_db()
    app.run(debug=True)