import dash
# Fusion des imports depuis dash
from dash import html, dcc, callback, callback_context, Input, Output, State, no_update
import dash_bootstrap_components as dbc
# from dash.dependencies import Input, Output, State # Plus nécessaire car importé de dash
import json
import os
import uuid
from datetime import datetime
import re # Import pour les expressions régulières

# Enregistrement de la page auprès de Dash Pages
dash.register_page(__name__, path='/reclamations')

DATA_FILE = "reclamations.json"  # Nom du fichier JSON

# --- Layout de la page (INCHANGÉ) ---
layout = dbc.Container([
    html.H1("Formulaire de Réclamation", className="text-center mt-4"),
    dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Nom et prénom :"),
                dbc.Input(id="reclamation-nom", type="text", placeholder="Votre nom et prénom", className="mb-3"),
            ], md=6),
            dbc.Col([
                dbc.Label("Email :"),
                # type="email" pour validation navigateur de base
                dbc.Input(id="reclamation-email", type="email", placeholder="Votre email", className="mb-3"),
            ], md=6),
        ]),
        dbc.Label("Description de la Réclamation :"),
        dbc.Textarea(id="reclamation-description", placeholder="Décrivez votre réclamation", className="mb-3"),
        dbc.Button("Soumettre", id="reclamation-submit", color="primary"),
        # La div où les messages succès/erreur seront affichés
        html.Div(id="reclamation-message", className="mt-3"),
    ]),
])


# --- Callback pour la soumission du formulaire AVEC VALIDATION ---
@callback(
    Output("reclamation-message", "children"),
    Input("reclamation-submit", "n_clicks"),
    State("reclamation-nom", "value"),
    State("reclamation-email", "value"),
    State("reclamation-description", "value"),
    prevent_initial_call=True
    )
def submit_reclamation(n_clicks, nom, email, description):
    # n_clicks n'est plus None grâce à prevent_initial_call, mais on garde la vérification
    if n_clicks is not None:

        # --- VALIDATION AMÉLIORÉE ---
        error_messages = [] # Liste pour collecter toutes les erreurs
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$" # Regex pour email

        # 1. Vérifier les champs vides (strip() enlève les espaces avant/après)
        if not nom or not nom.strip():
            error_messages.append("Le nom et prénom sont requis.")
        if not email or not email.strip():
            error_messages.append("L'adresse e-mail est requise.")
        else:
            # 2. Vérifier le format de l'email si non vide
            if not re.match(email_regex, email.strip()):
                error_messages.append("Le format de l'adresse e-mail est invalide.")

        if not description or not description.strip():
            error_messages.append("La description est requise.")

        # 3. S'il y a des erreurs, les afficher et arrêter
        if error_messages:
            return dbc.Alert(
                [html.P(msg, className="mb-0") for msg in error_messages], # Chaque erreur sur une ligne dans l'alerte
                color="warning",
                dismissable=True
            )
        # --- FIN VALIDATION AMÉLIORÉE ---

        # Si on arrive ici, toutes les validations sont passées
        # (Utiliser les valeurs nettoyées avec strip())
        nom_clean = nom.strip()
        email_clean = email.strip()
        description_clean = description.strip()

        now = datetime.now()
        date_heure = now.strftime("%d/%m/%Y %H:%M")

        reclamation = {
            "id": str(uuid.uuid4()),
            "nom": nom_clean,
            "email": email_clean, # Email validé
            "description": description_clean,
            "date": date_heure,
            "statut": "En attente"
        }
        try:
            reclamations = []
            if os.path.exists(DATA_FILE):
                if os.path.getsize(DATA_FILE) > 0:
                    with open(DATA_FILE, "r", encoding='utf-8') as f:
                        try:
                            reclamations = json.load(f)
                            if not isinstance(reclamations, list):
                                print(f"Avertissement: {DATA_FILE} ne contient pas une liste JSON. Réinitialisation.")
                                reclamations = []
                        except json.JSONDecodeError:
                            print(f"Avertissement: Erreur de décodage JSON dans {DATA_FILE}. Réinitialisation.")
                            reclamations = []

            reclamations.append(reclamation)

            with open(DATA_FILE, "w", encoding='utf-8') as f:
                json.dump(reclamations, f, indent=4, ensure_ascii=False)

            # Retourner un message succès clair
            return dbc.Alert("Réclamation soumise avec succès !", color="success", dismissable=True)

        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la réclamation : {e}")
            return dbc.Alert(f"Une erreur s'est produite lors de la sauvegarde. Veuillez réessayer.", color="danger", dismissable=True)

    # Si le callback est déclenché sans clic (ne devrait pas arriver avec prevent_initial_call)
    return no_update