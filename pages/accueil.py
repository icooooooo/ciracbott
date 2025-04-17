import dash
from dash import html, dcc, Input, Output, State, ALL, callback_context, callback
import dash_bootstrap_components as dbc
import json
from datetime import datetime
import os

# Assure-toi que Bootstrap Icons est chargé dans ton app principale :
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], use_pages=True)
# Le fichier CSS personnalisé dans assets/style.css sera chargé automatiquement.

dash.register_page(__name__, path='/') # Enregistrement de la page d'accueil

# --- Configuration ---
RATING_FILE = 'conversation_ratings.json' # Nom du fichier pour stocker les notes

# --- Fonction pour sauvegarder la note ---
def save_rating(rating_value):
    """Sauvegarde la note donnée dans un fichier JSON."""
    timestamp = datetime.now().isoformat()
    new_rating = {"rating": rating_value, "timestamp": timestamp}

    ratings_data = []
    if os.path.exists(RATING_FILE):
        try:
            with open(RATING_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    ratings_data = json.loads(content)
                    if not isinstance(ratings_data, list):
                        print(f"Avertissement : Le contenu de {RATING_FILE} n'est pas une liste JSON valide. Il sera écrasé.")
                        ratings_data = []
                else:
                     ratings_data = []
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Avertissement : Erreur de lecture/décodage de {RATING_FILE} ({e}). Un nouveau fichier sera créé ou le contenu sera écrasé.")
            ratings_data = []
        except Exception as e:
             print(f"Erreur inattendue lors de la lecture de {RATING_FILE}: {e}")
             ratings_data = []

    ratings_data.append(new_rating)

    try:
        with open(RATING_FILE, 'w', encoding='utf-8') as f:
            json.dump(ratings_data, f, indent=4, ensure_ascii=False)
        print(f"Note ({rating_value}) sauvegardée avec succès dans {RATING_FILE}")
    except IOError as e:
        print(f"Erreur lors de l'écriture dans le fichier {RATING_FILE}: {e}")
    except Exception as e:
        print(f"Erreur inattendue lors de l'écriture dans {RATING_FILE}: {e}")


# --- Contenu initial du widget de notation ---
def create_rating_stars():
    """Crée les éléments HTML pour les étoiles de notation."""
    return [
        html.P("Notez cette conversation :", style={'marginBottom': '5px', 'fontSize':'small'}),
        html.Div([
             dbc.Button(
                 html.I(className="bi bi-star-fill"),
                 id={'type': 'rating-star', 'index': i},
                 n_clicks=0,
                 color="warning",
                 outline=True,
                 size="sm",
                 className="me-1 border-0"
             )
             for i in range(1, 6)
        ])
    ]

# --- Layout de l'application ---
layout = dbc.Container([
    html.H1("Bienvenue sur CIRACbot", className="text-center mt-4"),
    html.P("Votre assistant bancaire intelligent", className="text-center"),

    # Chatbot Section
    dbc.Row([
        dbc.Col([
            html.Div(id="chatbot-container", children=[
                html.Div("👋 Bonjour ! Comment puis-je vous aider ?", className="chatbot-message chatbot-message-left"),
            ], className="chatbot-box chatbot-scroll-area"),
        ], width=12, md=10, lg=8)
    ], justify="center", className="mb-3"),

    # --- MODIFICATION ICI: Zone de saisie et icône "Envoyer" (Style comme l'image) ---
    html.Div(
        dbc.Row([
            dbc.Col([
                # Conteneur spécial pour l'input et l'icône (utilise les classes CSS de assets/style.css)
                html.Div(
                    [
                        dbc.Input(
                            id="user-input",      # ID pour récupérer la valeur dans le callback State
                            type="text",
                            placeholder="Écrivez votre message...",
                            autocomplete="off",
                            # La classe form-control est ajoutée par défaut par dbc.Input
                            # Le style (arrondi, padding) est géré par le CSS
                        ),
                        # L'icône cliquable, positionnée par CSS
                        html.I(
                            className="bi bi-send-fill send-icon", # Icône Bootstrap + classe CSS perso
                            id="send-btn",        # IMPORTANT: L'ID du bouton est maintenant sur l'icône
                            n_clicks=0,           # Nécessaire pour que l'icône déclenche le callback Input
                        )
                    ],
                    className="input-icon-container" # Applique la classe au conteneur
                )
            ], width=12, md=10, lg=8) # Ajuste la largeur comme avant
        ],
        justify="center" # Centre la colonne
        ),
        # Style pour fixer en bas (ajusté légèrement pour le padding)
        style={
            'position': 'fixed',
            'bottom': '0',
            'left': '0',
            'right': '0',
            'padding': '15px 10px', # Espace autour de l'input
            # 'backgroundColor': 'rgba(255, 255, 255, 0.95)', # Fond légèrement transparent
            # 'borderTop': '1px solid #e0e0e0', # Ligne de séparation
            'zIndex': '1000'
        }
    ),
    # --- FIN DE LA MODIFICATION ---

    # --- Section de Notation (Conteneur Principal) ---
    # Assure-toi que 'bottom' est suffisant pour être au-dessus de la barre de saisie
    html.Div(
        id="rating-widget",
        children=create_rating_stars(), # Contenu initial avec les étoiles
        style={
            'position': 'fixed',
            'bottom': '90px',  # REMONTÉ pour être au-dessus de la barre de saisie (ajuste si nécessaire)
            'right': '20px',
            'padding': '10px',
            'backgroundColor': '#f8f9fa',
            'border': '1px solid #ccc',
            'borderRadius': '5px',
            'zIndex': '1001',
            'textAlign': 'center',
            'minWidth': '180px'
        }
    ),

], fluid=True) # Ajoute du padding en bas du container principal pour éviter que le dernier message soit caché

# --- Callbacks (Inchangés car les IDs sont conservés) ---
@callback(
    Output("chatbot-container", "children"),
    Input("send-btn", "n_clicks"), # Déclenché par le clic sur l'icône html.I(id="send-btn")
    [State("user-input", "value"), # Récupère la valeur de dbc.Input(id="user-input")
    State("chatbot-container", "children")],
    prevent_initial_call=True
)
def update_chat(n_clicks, user_input, current_children):
    print("-" * 20)
    print(f"CALLBACK 'update_chat' DÉCLENCHÉ!")
    print(f"  n_clicks='{n_clicks}' (sur l'icône)")
    print(f"  user_input='{user_input}'")
    print(f"  Type initial de current_children: {type(current_children)}")
    print("-" * 20)
    if n_clicks and user_input:
        if not isinstance(current_children, list):
            print(f"  WARNING: current_children n'était pas une liste ({type(current_children)}). Conversion.")
            current_children = [current_children] if current_children else []
        user_message_div = html.Div(f"Vous: {user_input}", className="user-message chatbot-message-right")
        bot_response_div = html.Div("🤖 Bonjour et bienvenue sur CIRACBot, votre assistant bancaire intelligent disponible 24/7. Je suis actuellement en développement, revenez plus tard !", className="chatbot-message chatbot-message-left")
        current_children.append(user_message_div)
        current_children.append(bot_response_div)
        print(f"  Nouveaux messages ajoutés. Total enfants: {len(current_children)}")
        # Penser à ajouter un scroll automatique vers le bas si nécessaire (avec callback JS côté client)
        return current_children
    else:
        print("  Callback 'update_chat': Condition non remplie, retour dash.no_update")
        return dash.no_update

@callback(
    Output("rating-widget", "children"),
    Input({'type': 'rating-star', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_rating_submission(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered or not any(n > 0 for n in n_clicks_list):
        return dash.no_update

    if isinstance(ctx.triggered_id, dict) and 'index' in ctx.triggered_id:
        clicked_star_index = ctx.triggered_id['index']
        rating_value = int(clicked_star_index)
        save_rating(rating_value)
        feedback_message = f"Merci pour votre note de {rating_value} étoile{'s' if rating_value > 1 else ''} !"
        return html.P(feedback_message, style={'fontSize': 'small', 'margin': '0'})

    return dash.no_update