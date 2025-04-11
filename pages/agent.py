import dash
# Importer 'callback', 'no_update', etc.
from dash import html, dcc, Input, Output, State, ALL, callback, no_update, callback_context
import dash_bootstrap_components as dbc
# from dash.dependencies import Input, Output, State, ALL # Plus nécessaire
from dash.exceptions import PreventUpdate # Garder si utilisé, sinon no_update suffit
from flask_login import current_user
import json
import os
import uuid # Importer uuid si pas déjà fait (pour générer des clés uniques si besoin)
# import operator # Probablement pas nécessaire ici
from datetime import datetime

# --- Enregistrement de la page ---
dash.register_page(__name__, path='/agent')

DATA_FILE = "reclamations.json"
DEFAULT_SORT_COLUMN = "date"
DEFAULT_SORT_DIRECTION = False

# --- Layout de la page (Protection ajoutée) ---
def layout():
    if not current_user.is_authenticated:
        try:
            login_path = dash.page_registry['pages.login']['relative_path']
        except KeyError:
            login_path = '/login'
        return dcc.Location(pathname=login_path, id="agent-redirect-login")
    elif not hasattr(current_user, 'role') or current_user.role != 'admin':
        try:
            home_path = dash.page_registry['pages.accueil']['relative_path']
        except KeyError:
            home_path = '/'
        return dbc.Container([
            html.H1("Accès Refusé", className="text-danger text-center mt-5"),
            html.P("Vous devez être administrateur pour accéder à cette page.", className="text-center"),
            dbc.Button("Retour à l'accueil", href=home_path, color="primary", className="d-block mx-auto mt-3")
        ])
    else:
        # Si admin connecté, afficher le layout normal
        return dbc.Container([
            html.H1("Interface Agent", className="text-center mt-4"),
            dbc.Tabs([
                dbc.Tab(label="Dashboard", tab_id="dashboard"),
                dbc.Tab(label="Gestion des comptes clients", tab_id="gestion-comptes"),
                dbc.Tab(label="Suivi des réclamations", tab_id="suivi-reclamations"),
            ], id="agent-tabs", active_tab="suivi-reclamations"), # Onglet par défaut
            html.Div(id="agent-content", className="mt-3"),
            dcc.Store(id="sort-state", data={"column": DEFAULT_SORT_COLUMN, "direction": DEFAULT_SORT_DIRECTION}),
            # Le conteneur modal reste ici, mais le modal lui-même sera généré dynamiquement
            html.Div(id="modal-container")
        ], fluid=True)

# --- Fonctions pour générer le contenu des onglets ---
def dashboard_tab():
    # --- REMETTRE VOTRE CODE ORIGINAL ICI ---
    return dbc.Card(
        dbc.CardBody([
            html.H4("Dashboard", className="card-title"),
            dbc.Row([
                dbc.Col([html.H6("Taux de satisfaction client :"), html.P("85%")], md=6), # Exemple de valeur
                dbc.Col([html.H6("Taux moyen de réponse :"), html.P("2 minutes")], md=6), # Exemple
            ]),
            dbc.Row([
                dbc.Col([html.H6("Taux d'escalade :"), html.P("5%")], md=6), # Exemple
                dbc.Col([html.H6("Taux de résolution en première interaction :"), html.P("70%")], md=6), # Exemple
            ]),
            # Ajoutez d'autres statistiques ou graphiques si vous en aviez
        ])
    )

def gestion_comptes_tab():
    # --- REMETTRE VOTRE CODE ORIGINAL ICI ---
    return dbc.Card(
        dbc.CardBody([
            html.H4("Gestion des comptes clients", className="card-title"),
            dbc.Label("Rechercher un compte par email :"),
            dbc.Input(type="email", id="recherche-email", placeholder="Email du client", className="mb-3"),
            dbc.Button("Rechercher", id="bouton-rechercher", color="primary", className="mr-1"), # ou me-1 avec Bootstrap 5
            # La div où les résultats de la recherche s'afficheront (via un autre callback si nécessaire)
            html.Div(id="resultat-recherche", className="mt-3"),
        ])
    )

def suivi_reclamations_tab(sort_state):
    # ... (code inchangé, mais s'assurer que les boutons 'Voir' ont le bon ID à motif) ...
    sort_column = sort_state.get("column", DEFAULT_SORT_COLUMN)
    sort_direction = sort_state.get("direction", DEFAULT_SORT_DIRECTION)
    reclamations = []
    if os.path.exists(DATA_FILE):
        if os.path.getsize(DATA_FILE) > 0:
             with open(DATA_FILE, "r", encoding='utf-8') as f:
                try:
                    reclamations = json.load(f)
                    if not isinstance(reclamations, list): reclamations = []
                except json.JSONDecodeError: reclamations = []

    try:
        reclamations.sort(
            key=lambda r: datetime.strptime(r.get("date", "01/01/1900 00:00"), "%d/%m/%Y %H:%M")
            if sort_column == "date" and r.get("date") else str(r.get(sort_column, '')).lower(),
            reverse=sort_direction
        )
    except (ValueError, TypeError) as e:
        print(f"Erreur lors du tri dans agent.py : {e}")

    table_header = [
        html.Thead(html.Tr([
            html.Th(dbc.Button("Nom", id={'type': 'sort-button', 'column': 'nom'}, color="link", className="p-0")),
            html.Th(dbc.Button("Date", id={'type': 'sort-button', 'column': 'date'}, color="link", className="p-0")),
            html.Th("Statut"),
            html.Th("Action"),
        ]))
    ]
    if not reclamations:
         table_body = [html.Tbody(html.Tr(html.Td("Aucune réclamation trouvée.", colSpan=4, className="text-center")))]
    else:
        table_body = [
            html.Tbody([
                html.Tr([
                    html.Td(r.get("nom", "N/A")),
                    html.Td(r.get("date", "N/A")),
                    html.Td(r.get("statut", "N/A")),
                    # S'assurer que l'ID du bouton "Voir" est bien à motif
                    html.Td(dbc.Button("Voir", color="primary", size="sm", id={"type": "voir-reclamation", "index": r.get("id", uuid.uuid4())})) # Générer clé unique si id manque
                # Utiliser une clé unique pour chaque ligne
                ], key=r.get("id", f"row-{i}")) for i, r in enumerate(reclamations) # if r.get("id") # S'assurer que chaque réclamation a un id
            ])
        ]

    table = dbc.Table(table_header + table_body, bordered=True, striped=True, hover=True, responsive=True)
    return dbc.Card(dbc.CardBody([html.H4("Suivi des réclamations"), table]))

# --- Callbacks ---

# Callback pour afficher le contenu de l'onglet actif (INCHANGÉ)
@callback(
    Output("agent-content", "children"),
    Input("agent-tabs", "active_tab"),
    Input("sort-state", "data"),
)
def render_tab_content(active_tab, sort_state):
    if not current_user.is_authenticated or current_user.role != 'admin':
         return no_update
    if active_tab == "dashboard":
        return dashboard_tab()
    elif active_tab == "gestion-comptes":
        return gestion_comptes_tab()
    elif active_tab == "suivi-reclamations":
        return suivi_reclamations_tab(sort_state or {"column": DEFAULT_SORT_COLUMN, "direction": DEFAULT_SORT_DIRECTION})
    return html.P("Onglet non trouvé")

# --- NOUVELLE APPROCHE POUR LE MODAL ---

# Callback 1 : Ouvre le modal et affiche les détails
@callback(
    Output("modal-container", "children"), # Sortie : le conteneur qui tiendra le modal
    Input({"type": "voir-reclamation", "index": ALL}, "n_clicks"), # Entrée : Clic sur N'IMPORTE quel bouton "Voir"
    prevent_initial_call=True
)
def display_reclamation_modal(n_clicks):
    ctx = callback_context
    # Vérifier si un bouton "Voir" a réellement été cliqué (et non un autre callback)
    if not ctx.triggered or not any(click for click in n_clicks if click):
        return no_update

    # Obtenir l'ID complet du bouton cliqué
    triggered_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        # Extraire l'index (ID de la réclamation) de l'ID du bouton
        triggered_id_dict = json.loads(triggered_id_str.replace("'", "\""))
        if isinstance(triggered_id_dict, dict) and triggered_id_dict.get("type") == "voir-reclamation":
            reclamation_id = triggered_id_dict.get("index")
            if not reclamation_id: return no_update # Pas d'index trouvé

            # --- Charger et trouver la réclamation ---
            reclamations = []
            if os.path.exists(DATA_FILE):
                 if os.path.getsize(DATA_FILE) > 0:
                    with open(DATA_FILE, "r", encoding='utf-8') as f:
                        try:
                            reclamations = json.load(f)
                            if not isinstance(reclamations, list): reclamations = []
                        except json.JSONDecodeError: reclamations = []
            reclamation = next((r for r in reclamations if r.get("id") == reclamation_id), None)
            # --- Fin chargement ---

            if not reclamation:
                return dbc.Alert(f"Réclamation ID {reclamation_id} non trouvée.", color="warning", duration=4000)

            # --- Créer le composant Modal ---
            # Important : Le Modal lui-même et le bouton Fermer ont des ID fixes
            modal = dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(f"Détails - {reclamation.get('nom', 'N/A')}")),
                    dbc.ModalBody([
                        html.Strong("Date: "), html.P(reclamation.get('date', 'N/A')),
                        html.Strong("Email: "), html.P(reclamation.get('email', 'N/A')),
                        html.Strong("Statut: "), html.P(reclamation.get('statut', 'N/A')),
                        html.Hr(),
                        html.Strong("Description:"),
                        html.P(reclamation.get('description', 'N/A'), style={'whiteSpace': 'pre-wrap'})
                    ]),
                    dbc.ModalFooter(
                        # ID fixe pour le bouton fermer
                        dbc.Button("Fermer", id="agent-close-modal-button", className="ms-auto")
                    ),
                ],
                id="agent-reclamation-detail-modal", # ID fixe pour le modal
                is_open=True, # Ouvrir le modal lors de sa création
                size="lg"
            )
            # Retourner le modal pour l'afficher dans "modal-container"
            return modal
        else:
            return no_update # L'ID déclencheur n'était pas un bouton "Voir"
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Erreur parsing ID modal: {e}, triggered_id: {triggered_id_str}")
        return no_update


# Callback 2 : Ferme le modal
@callback(
    Output("agent-reclamation-detail-modal", "is_open"), # Sortie : propriété is_open du modal
    Input("agent-close-modal-button", "n_clicks"),     # Entrée : clic sur le bouton Fermer
    State("agent-reclamation-detail-modal", "is_open"),# Entrée : état actuel du modal
    prevent_initial_call=True
)
def close_reclamation_modal(n_clicks, is_open):
    # Si le bouton est cliqué ET que le modal est actuellement ouvert
    if n_clicks and is_open:
        return False # Retourner False pour fermer le modal (mettre is_open à False)
    # Sinon, ne rien faire (ne pas changer l'état is_open)
    return no_update


# Callback pour le tri de la table (INCHANGÉ, mais vérifier les ID)
@callback(
    Output("sort-state", "data"),
    Input({'type': 'sort-button', 'column': ALL}, 'n_clicks'), # Utilise le nouvel ID à motif
    State("sort-state", "data"),
    prevent_initial_call=True
)
def sort_table(sort_clicks, sort_state):
    ctx = callback_context
    if not ctx.triggered or not any(click for click in sort_clicks if click):
        return no_update

    triggered_id_str = ctx.triggered[0]["prop_id"].split(".")[0]
    try:
        triggered_id_dict = json.loads(triggered_id_str.replace("'", "\""))
        if isinstance(triggered_id_dict, dict) and triggered_id_dict.get("type") == "sort-button":
            column = triggered_id_dict.get("column")
            if not column: return no_update

            current_column = sort_state.get("column", DEFAULT_SORT_COLUMN)
            current_direction = sort_state.get("direction", DEFAULT_SORT_DIRECTION)

            if column == current_column:
                new_direction = not current_direction
            else:
                new_direction = False

            new_sort_state = {"column": column, "direction": new_direction}
            print(f"Nouveau tri demandé (Agent): {new_sort_state}")
            return new_sort_state
        else:
            return no_update
    except (json.JSONDecodeError, TypeError, ValueError) as e:
         print(f"Erreur parsing ID sort: {e}, triggered_id: {triggered_id_str}")
         return no_update