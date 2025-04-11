import dash
# Fusion et ajout des imports nécessaires depuis dash
from dash import dcc, html, Input, Output, State, callback_context, callback, no_update
import dash_bootstrap_components as dbc
# from dash.dependencies import Input, Output, State, callback_context # Plus nécessaire
import json
import os

# --- Enregistrement de la page ---
# Définit l'URL pour accéder à cette page, par ex: /parametres
dash.register_page(__name__, path='/parametres') # <-- AJOUTÉ

# --- Gestion des Préférences (inchangée) ---
PREFERENCES_FILE = "preferences.json"
DEFAULT_PREFERENCES = {"theme": "light", "language": "fr"}

def load_preferences():
    """Charge les préférences utilisateur depuis le fichier."""
    if not os.path.exists(PREFERENCES_FILE):
        return DEFAULT_PREFERENCES.copy()
    try:
        with open(PREFERENCES_FILE, "r", encoding='utf-8') as f:
            content = f.read()
            if not content:
                return DEFAULT_PREFERENCES.copy()
            preferences = json.loads(content)
            # Assurer que toutes les clés par défaut existent
            for key, value in DEFAULT_PREFERENCES.items():
                preferences.setdefault(key, value)
            return preferences
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erreur lors de la lecture de {PREFERENCES_FILE}: {e}. Utilisation des préférences par défaut.")
        return DEFAULT_PREFERENCES.copy()

def save_preferences(preferences):
    """Enregistre les préférences utilisateur dans le fichier."""
    try:
        with open(PREFERENCES_FILE, "w", encoding='utf-8') as f:
            json.dump(preferences, f, indent=4, ensure_ascii=False)
        print(f"Préférences sauvegardées: {preferences}")
    except IOError as e:
        print(f"Erreur lors de l'écriture dans {PREFERENCES_FILE}: {e}")

# --- Layout Principal de la Page Paramètres (inchangé) ---
layout = dbc.Container([
    html.H1("Paramètres du Compte", className="text-center mt-4"),
    dbc.Tabs([
        dbc.Tab(label="Informations personnelles", tab_id="informations-personnelles"),
        dbc.Tab(label="Sécurité et connexion", tab_id="securite-connexion"),
        dbc.Tab(label="Préférences utilisateur", tab_id="preferences-utilisateur"),
    ], id="parametres-tabs", active_tab="preferences-utilisateur"), # Active l'onglet Prefs par défaut
    html.Div(id="parametres-content", className="mt-3"),
])

# --- Fonctions pour générer le contenu des onglets (inchangées) ---

def informations_personnelles_tab():
    # ... (votre code pour cet onglet)
    return dbc.Card(dbc.CardBody([html.H4("Informations personnelles"), html.P("Contenu info perso...")]))

def securite_connexion_tab():
    # ... (votre code pour cet onglet)
     return dbc.Card(dbc.CardBody([html.H4("Sécurité et connexion"), html.P("Contenu sécurité...")]))

def preferences_utilisateur_tab():
    preferences = load_preferences()
    theme = preferences.get("theme", DEFAULT_PREFERENCES["theme"])
    language = preferences.get("language", DEFAULT_PREFERENCES["language"])
    return dbc.Card(
        dbc.CardBody([
            html.H4("Préférences utilisateur", className="card-title"),
            html.P("Ici, vous pouvez modifier vos préférences utilisateur."),
            dbc.Label("Thème :"),
            dcc.Dropdown(
                id="theme-dropdown",
                options=[
                    {"label": "Clair", "value": "light"},
                    {"label": "Sombre", "value": "dark"},
                ],
                value=theme,
                clearable=False,
            ),
            dbc.Label("Langue :", className="mt-3"),
            dcc.Dropdown(
                id="language-dropdown",
                options=[
                    {"label": "Français", "value": "fr"},
                    {"label": "Anglais", "value": "en"},
                ],
                value=language,
                clearable=False,
            ),
            # Div pour afficher les messages de confirmation
            html.Div(id="preferences-feedback", className="mt-3 text-success small")
        ])
    )

# --- Callbacks (maintenant au niveau supérieur avec le décorateur @callback) ---

# Callback pour afficher le contenu de l'onglet actif
@callback(
    Output("parametres-content", "children"),
    Input("parametres-tabs", "active_tab")
)
def render_tab_content(active_tab):
    # La logique interne est inchangée
    if active_tab == "informations-personnelles":
        return informations_personnelles_tab()
    elif active_tab == "securite-connexion":
        return securite_connexion_tab()
    elif active_tab == "preferences-utilisateur":
        return preferences_utilisateur_tab()
    return html.P("Contenu non trouvé") # Fallback

# --- Callback pour gérer les préférences ---
@callback(
    Output("theme-store", "data"),             # Met à jour le store (utilisé par app.py pour le thème global)
    Output("preferences-feedback", "children"),# Affiche le feedback dans l'onglet
    Input("theme-dropdown", "value"),
    Input("language-dropdown", "value"),
    prevent_initial_call=True,
)
def update_preferences_and_theme(selected_theme, selected_language):
    ctx = callback_context # Utiliser la variable importée directement
    triggered_id = ctx.triggered_id

    if not triggered_id:
        print("Callback préférences déclenché sans input spécifique.")
        # Utiliser no_update importé de dash
        return no_update, no_update

    # Charger les préférences actuelles
    preferences = load_preferences()
    feedback_message = ""
    theme_to_store = no_update # Par défaut, on ne met pas à jour le store

    # Mettre à jour la préférence qui a changé
    if triggered_id == "theme-dropdown":
        print(f"Theme dropdown changed to: {selected_theme}")
        preferences["theme"] = selected_theme
        theme_to_store = selected_theme # Préparer la mise à jour du store
        feedback_message = f"Thème '{selected_theme}' appliqué et enregistré."
    elif triggered_id == "language-dropdown":
        print(f"Language dropdown changed to: {selected_language}")
        preferences["language"] = selected_language
        feedback_message = f"Langue '{selected_language}' enregistrée."
        # Pas de mise à jour du store de thème si seule la langue change

    # Sauvegarder les préférences mises à jour
    save_preferences(preferences)

    # Retourner la valeur pour le store et le message de feedback
    return theme_to_store, feedback_message