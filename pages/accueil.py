import dash
from dash import html, dcc, Input, Output, State, ALL, callback_context,callback
import dash_bootstrap_components as dbc
import json
from datetime import datetime
import os
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
                # Vérifier si le fichier n'est pas vide avant de charger
                content = f.read()
                if content:
                    ratings_data = json.loads(content)
                    if not isinstance(ratings_data, list):
                        print(f"Avertissement : Le contenu de {RATING_FILE} n'est pas une liste JSON valide. Il sera écrasé.")
                        ratings_data = []
                else:
                    # Fichier vide, initialiser comme liste vide
                     ratings_data = []
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Avertissement : Erreur de lecture/décodage de {RATING_FILE} ({e}). Un nouveau fichier sera créé ou le contenu sera écrasé.")
            ratings_data = []
        except Exception as e: # Attraper d'autres erreurs potentielles
             print(f"Erreur inattendue lors de la lecture de {RATING_FILE}: {e}")
             ratings_data = [] # Réinitialiser en cas d'erreur grave
            
    ratings_data.append(new_rating)
    
    try:
        with open(RATING_FILE, 'w', encoding='utf-8') as f:
            json.dump(ratings_data, f, indent=4, ensure_ascii=False)
        print(f"Note ({rating_value}) sauvegardée avec succès dans {RATING_FILE}")
    except IOError as e:
        print(f"Erreur lors de l'écriture dans le fichier {RATING_FILE}: {e}")
    except Exception as e: # Attraper d'autres erreurs potentielles
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
            ], className="chatbot-box"),
        ], width=6)
    ], justify="center"),

    # Zone de saisie et bouton "Envoyer"
    dbc.Row([
        dbc.Col([
            dbc.InputGroup(
                [
                    dcc.Input(id="user-input", type="text", placeholder="Écrivez votre message...", className="form-control"),
                    dbc.Button("Envoyer", id="send-btn", color="primary") 
                ],
            ),
        ], width=10, lg=6),
    ], 
    justify="center",
    style={'position': 'fixed', 'bottom': '20px', 'left': '0', 'right': '0', 'padding': '10px 0', 'zIndex': '1000'} 
    ),

    # --- Section de Notation (Conteneur Principal) ---
    html.Div(
        id="rating-widget",
        children=create_rating_stars(), # Contenu initial avec les étoiles
        style={
            'position': 'fixed',
            'bottom': '100px',
            'right': '20px',
            'padding': '10px',
            'backgroundColor': '#f8f9fa',
            'border': '1px solid #ccc',
            'borderRadius': '5px',
            'zIndex': '1001', 
            'textAlign': 'center',
            'minWidth': '180px' # Donner une largeur minimale pour une meilleure apparence
        }
    ),

], fluid=True)

# --- Callbacks ---
@callback(
    Output("chatbot-container", "children"),
    Input("send-btn", "n_clicks"),
    [State("user-input", "value"),
     State("chatbot-container", "children")],
    prevent_initial_call=True
)
def update_chat(n_clicks, user_input, current_children):
    print("-" * 20) # Séparateur
    print(f"CALLBACK 'update_chat' DÉCLENCHÉ!")
    print(f"  n_clicks='{n_clicks}'")
    print(f"  user_input='{user_input}'")
    print(f"  Type initial de current_children: {type(current_children)}") # Voir le type initial
    print("-" * 20)

    # Condition pour ajouter des messages : clic ET message non vide
    if n_clicks and user_input:

        # S'assurer que current_children est une liste
        if not isinstance(current_children, list):
             print(f"  WARNING: current_children n'était pas une liste ({type(current_children)}). Conversion.")
             current_children = [current_children] if current_children else []

        # --- LOGIQUE MANQUANTE RESTAURÉE ---
        # Créer les Div pour le message utilisateur et la réponse du bot
        user_message_div = html.Div(f"Vous: {user_input}", className="user-message chatbot-message-right")
        # Vous pouvez mettre ici une logique plus avancée pour la réponse du bot si nécessaire
        bot_response_div = html.Div("🤖 Bonjour et bienvenue sur CIRACBot, votre assistant bancaire intelligent disponible 24/7. Je suis actuellement en développement, revenez plus tard !", className="chatbot-message chatbot-message-left")

        # Ajouter les nouveaux messages à la liste existante
        current_children.append(user_message_div)
        current_children.append(bot_response_div)
        print(f"  Nouveaux messages ajoutés. Total enfants: {len(current_children)}")
        # --- FIN DE LA LOGIQUE RESTAURÉE ---

        # Retourner la liste COMPLÈTE (anciens + nouveaux messages)
        return current_children

    else:
        # Si on n'a pas cliqué ou si l'input est vide, ne rien changer
        print("  Callback 'update_chat': Condition non remplie, retour dash.no_update")
        return dash.no_update
# Callback pour la notation
@callback(
    Output("rating-widget", "children"),
    Input({'type': 'rating-star', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_rating_submission(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered or not any(n > 0 for n in n_clicks_list):
        return dash.no_update

    # Assurer que triggered_id est bien un dictionnaire (ID à motif)
    if isinstance(ctx.triggered_id, dict) and 'index' in ctx.triggered_id:
        clicked_star_index = ctx.triggered_id['index']
        rating_value = int(clicked_star_index)

        # Sauvegarder la note
        save_rating(rating_value)

        # --- AJOUTER CETTE LIGNE CI-DESSOUS ---
        feedback_message = f"Merci pour votre note de {rating_value} étoile{'s' if rating_value > 1 else ''} !"
        # --- FIN DE L'AJOUT ---

        # Retourner le message pour remplacer le contenu du widget
        # Maintenant, 'feedback_message' existe quand cette ligne est exécutée
        return html.P(feedback_message, style={'fontSize': 'small', 'margin': '0'})

    return dash.no_update