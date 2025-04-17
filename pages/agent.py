import dash

from dash import html, dcc, Input, Output, State, ALL, callback, no_update, callback_context, MATCH
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate 
from flask_login import current_user
import json
import os
import uuid
from datetime import datetime
import sqlite3 
# --- Enregistrement de la page ---
dash.register_page(__name__, path='/agent')

DATA_FILE = "reclamations.json"
DB_FILE = "ciracbot.db" # <-- Chemin vers ta base de données SQLite
DEFAULT_SORT_COLUMN = "date"
DEFAULT_SORT_DIRECTION = False

# --- Définition des rôles possibles ---
AVAILABLE_ROLES = ['utilisateur', 'admin'] # Adapte si tes rôles sont différents
def layout():
    # ... (code du layout inchangé, s'assurer qu'il contient les stores et modals nécessaires) ...
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
            ], id="agent-tabs", active_tab="suivi-reclamations"),
            html.Div(id="agent-content", className="mt-3"),
            dcc.Store(id="sort-state", data={"column": DEFAULT_SORT_COLUMN, "direction": DEFAULT_SORT_DIRECTION}),
            html.Div(id="modal-container"), # Pour le modal des détails réclamation
            # Stores et Modals pour la suppression (inchangés)
            dcc.Store(id='store-delete-target-client-id', data=None),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Confirmation de suppression")),
                    dbc.ModalBody(id="delete-client-modal-body", children="Êtes-vous sûr de vouloir supprimer ce compte ? Cette action est irréversible."),
                    dbc.ModalFooter([
                        dbc.Button("Annuler", id="cancel-delete-client-button", color="secondary"),
                        dbc.Button("Confirmer la suppression", id="confirm-delete-client-button", color="danger"),
                    ]),
                ],
                id="delete-client-confirmation-modal",
                is_open=False,
                backdrop="static",
            ),
        ], fluid=True)


# --- Fonctions pour générer le contenu des onglets ---
# ... (dashboard_tab, gestion_comptes_tab, suivi_reclamations_tab restent inchangées dans leur structure) ...
def dashboard_tab():
    return dbc.Card(
        dbc.CardBody([
            html.H4("Dashboard", className="card-title"),
            dbc.Row([
                dbc.Col([html.H6("Taux de satisfaction client :"), html.P("85%")], md=6),
                dbc.Col([html.H6("Taux moyen de réponse :"), html.P("2 minutes")], md=6),
            ]),
            dbc.Row([
                dbc.Col([html.H6("Taux d'escalade :"), html.P("5%")], md=6),
                dbc.Col([html.H6("Taux de résolution en première interaction :"), html.P("70%")], md=6),
            ]),
        ])
    )

def gestion_comptes_tab():
     return dbc.Card(
        dbc.CardBody([
            html.H4("Gestion des comptes clients", className="card-title"),
            dbc.Label("Rechercher un compte par email :"),
            dbc.Input(type="email", id="recherche-email", placeholder="Email du client", className="mb-3"),
            dbc.Button("Rechercher", id="bouton-rechercher", color="primary", className="mr-1"),
            html.Div(id="resultat-recherche", className="mt-3"),
        ])
    )

def suivi_reclamations_tab(sort_state):
    # ... (code inchangé) ...
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
            key=lambda r: (
                datetime.strptime(r.get("date", "01/01/1900 00:00"), "%d/%m/%Y %H:%M")
                if sort_column == "date" and r.get("date")
                else str(val) if (val := r.get(sort_column)) is not None and isinstance(val, (int, float))
                else str(val).lower() if (val := r.get(sort_column)) is not None
                else ""
            ),
            reverse=sort_direction
        )
    except (ValueError, TypeError, AttributeError) as e:
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
                    html.Td(dbc.Button("Voir", color="primary", size="sm", id={"type": "voir-reclamation", "index": r.get("id", f"gen-{i}")}))
                ], key=r.get("id", f"row-{i}")) for i, r in enumerate(reclamations)
            ])
        ]
    table = dbc.Table(table_header + table_body, bordered=True, striped=True, hover=True, responsive=True)
    return dbc.Card(dbc.CardBody([html.H4("Suivi des réclamations"), table]))

# =======================================================================
# === FONCTIONS DE BASE DE DONNÉES (Recherche + MAJ Rôle + Suppression) ===
# =======================================================================

def find_client_by_email(email_address):
    # ... (Fonction find_client_by_email précédente, utilisant sqlite3, inchangée) ...
    conn = None
    TABLE_NAME = 'users' # Adapte si nécessaire
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql_query = f"""
            SELECT id, username, email, role
            FROM {TABLE_NAME} WHERE email = ?
        """
        cursor.execute(sql_query, (email_address,))
        result_row = cursor.fetchone()
        if result_row:
            account_data = {
                "id_client": result_row["id"],
                "username": result_row["username"],
                "email": result_row["email"],
                "role": result_row["role"]
            }
            print(f"Données trouvées en BDD : {account_data}")
            return account_data
        else:
            print(f"Email {email_address} non trouvé dans la table '{TABLE_NAME}'.")
            return None
    except sqlite3.Error as e:
        print(f"Erreur lors de l'accès à la base de données SQLite ('{TABLE_NAME}') : {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_client_by_id(client_id):
    # ... (Fonction delete_client_by_id précédente, utilisant sqlite3, inchangée) ...
    conn = None
    TABLE_NAME = 'users' # Adapte si nécessaire
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        sql_query = f"DELETE FROM {TABLE_NAME} WHERE id = ?"
        cursor.execute(sql_query, (client_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Client ID {client_id} supprimé avec succès de la table '{TABLE_NAME}'.")
            return True
        else:
            print(f"Aucun client trouvé avec l'ID {client_id} dans '{TABLE_NAME}' pour suppression.")
            return False
    except sqlite3.Error as e:
        print(f"Erreur lors de la suppression dans la base de données SQLite ('{TABLE_NAME}') : {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_client_role_in_db(client_id, new_role):
    # ... (Fonction update_client_role_in_db précédente, utilisant sqlite3, inchangée) ...
    if new_role not in AVAILABLE_ROLES:
        print(f"Erreur: Rôle '{new_role}' non valide.")
        return False
    conn = None
    TABLE_NAME = 'users' # Adapte si nécessaire
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        sql_query = f"UPDATE {TABLE_NAME} SET role = ? WHERE id = ?"
        cursor.execute(sql_query, (new_role, client_id))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Rôle du client ID {client_id} mis à jour à '{new_role}' dans '{TABLE_NAME}'.")
            return True
        else:
            print(f"Aucun client trouvé avec l'ID {client_id} dans '{TABLE_NAME}' pour mise à jour du rôle.")
            return False
    except sqlite3.Error as e:
        print(f"Erreur lors de la mise à jour du rôle dans la BDD SQLite ('{TABLE_NAME}') : {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- Callbacks ---

# Callback pour afficher le contenu de l'onglet actif (INCHANGÉ)
@callback(
    Output("agent-content", "children"),
    Input("agent-tabs", "active_tab"),
    Input("sort-state", "data"),
)
def render_tab_content(active_tab, sort_state):
    # ... (code inchangé) ...
    if not current_user.is_authenticated or current_user.role != 'admin':
         return no_update
    if active_tab == "dashboard":
        return dashboard_tab()
    elif active_tab == "gestion-comptes":
        return gestion_comptes_tab()
    elif active_tab == "suivi-reclamations":
        return suivi_reclamations_tab(sort_state or {"column": DEFAULT_SORT_COLUMN, "direction": DEFAULT_SORT_DIRECTION})
    return html.P("Onglet non trouvé")

# Callbacks pour le modal de détails réclamation (INCHANGÉS)
@callback(
    Output("modal-container", "children"),
    Input({"type": "voir-reclamation", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def display_reclamation_modal(n_clicks):
     # ... (code inchangé) ...
    ctx = callback_context
    if not ctx.triggered or not any(click for click in n_clicks if click):
        return no_update
    triggered_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_id_dict = json.loads(triggered_id_str.replace("'", "\""))
        if isinstance(triggered_id_dict, dict) and triggered_id_dict.get("type") == "voir-reclamation":
            reclamation_id = triggered_id_dict.get("index")
            if not reclamation_id: return no_update
            reclamations = []
            if os.path.exists(DATA_FILE):
                 if os.path.getsize(DATA_FILE) > 0:
                    with open(DATA_FILE, "r", encoding='utf-8') as f:
                        try:
                            reclamations = json.load(f)
                            if not isinstance(reclamations, list): reclamations = []
                        except json.JSONDecodeError: reclamations = []
            reclamation = next((r for r in reclamations if r.get("id") == reclamation_id), None)
            if not reclamation:
                return dbc.Alert(f"Réclamation ID {reclamation_id} non trouvée.", color="warning", duration=4000)
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
                        dbc.Button("Fermer", id="agent-close-modal-button", className="ms-auto")
                    ),
                ],
                id="agent-reclamation-detail-modal",
                is_open=True,
                size="lg"
            )
            return modal
        else:
            return no_update
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Erreur parsing ID modal: {e}, triggered_id: {triggered_id_str}")
        return no_update

@callback(
    Output("agent-reclamation-detail-modal", "is_open"),
    Input("agent-close-modal-button", "n_clicks"),
    State("agent-reclamation-detail-modal", "is_open"),
    prevent_initial_call=True
)
def close_reclamation_modal(n_clicks, is_open):
     # ... (code inchangé) ...
    if n_clicks and is_open:
        return False
    return no_update

# Callback pour le tri de la table (INCHANGÉ)
@callback(
    Output("sort-state", "data"),
    Input({'type': 'sort-button', 'column': ALL}, 'n_clicks'),
    State("sort-state", "data"),
    prevent_initial_call=True
)
def sort_table(sort_clicks, sort_state):
    # ... (code inchangé) ...
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

# ==================================================================
# === CALLBACK POUR LA RECHERCHE EMAIL (MODIFIÉ POUR DROPDOWN RÔLE) ===
# ==================================================================
@callback(
    Output("resultat-recherche", "children"),
    Input("bouton-rechercher", "n_clicks"),
    Input("recherche-email", "n_submit"),
    State("recherche-email", "value"),
    prevent_initial_call=True
)
def search_client_account(n_clicks, n_submit, email_to_search):
    # ... (code de recherche et affichage modifié pour inclure le dropdown et bouton Enregistrer rôle) ...
    triggered_id = callback_context.triggered_id
    if (triggered_id == "bouton-rechercher" or triggered_id == "recherche-email") and email_to_search:
        print(f"Recherche du compte pour l'email : {email_to_search}")
        account_data = find_client_by_email(email_to_search)

        if account_data:
            client_id = account_data.get('id_client')
            current_role = account_data.get('role')

            result_layout = dbc.Card(dbc.CardBody([
                html.H5("Compte trouvé", className="card-title"),
                dbc.ListGroup([
                    dbc.ListGroupItem(f"ID Client : {client_id}"),
                    dbc.ListGroupItem(f"Nom d'utilisateur : {account_data.get('username', 'N/A')}"),
                    dbc.ListGroupItem(f"Email : {account_data.get('email', 'N/A')}"),
                    dbc.ListGroupItem([
                        "Rôle : ",
                        dbc.Select(
                            id={'type': 'role-select', 'index': client_id},
                            options=[
                                {'label': role.capitalize(), 'value': role} for role in AVAILABLE_ROLES
                            ],
                            value=current_role if current_role in AVAILABLE_ROLES else None,
                            placeholder="Choisir un rôle..." if current_role not in AVAILABLE_ROLES else None,
                            size="sm",
                            style={'display': 'inline-block', 'width': 'auto', 'marginLeft': '10px'}
                        ),
                        dbc.Button(
                            "Enregistrer le rôle",
                            id={'type': 'save-role-btn', 'index': client_id},
                            color="success",
                            size="sm",
                            className="ms-2"
                        )
                    ]),
                ], flush=True, className="mb-3"),
                dbc.Button(
                    "Supprimer ce compte",
                    id={'type': 'delete-client-open-modal-btn', 'index': client_id},
                    color="danger",
                    size="sm",
                    className="mt-2"
                )
            ]), className="mt-3")
            return result_layout
        else:
            return dbc.Alert(f"Aucun compte trouvé pour l'adresse e-mail : {email_to_search}", color="warning", className="mt-3")
    elif (triggered_id == "bouton-rechercher" or triggered_id == "recherche-email") and not email_to_search:
        return dbc.Alert("Veuillez entrer une adresse e-mail à rechercher.", color="info", className="mt-3")
    else:
        return no_update


# ============================================================
# === CALLBACK POUR LA MISE À JOUR DU RÔLE (CORRIGÉ) ===
# ============================================================
@callback(
    # Sortie : Met à jour la zone de résultat avec un message de succès/erreur
    Output("resultat-recherche", "children", allow_duplicate=True),
    # Entrée : Clic sur N'IMPORTE quel bouton "Enregistrer le rôle"
    Input({"type": "save-role-btn", "index": ALL}, "n_clicks"),
    # State : Lire les valeurs de TOUS les dropdowns visibles
    State({"type": "role-select", "index": ALL}, "value"),
    # State : Lire les IDs de TOUS les dropdowns visibles (pour faire le lien)
    State({"type": "role-select", "index": ALL}, "id"),
    prevent_initial_call=True
)
def update_client_role(save_btn_n_clicks, role_select_values, role_select_ids):
    triggered = callback_context.triggered
    # Vérifier si un des boutons "Enregistrer" a été cliqué
    if not triggered or not any(click for click in save_btn_n_clicks if click):
        return no_update

    # Obtenir l'ID du bouton qui a déclenché le callback
    triggered_button_id_dict = callback_context.triggered_id
    # Vérifier si l'ID est bien celui attendu
    if not isinstance(triggered_button_id_dict, dict) or triggered_button_id_dict.get("type") != "save-role-btn":
        return no_update # Déclenché par autre chose

    # Extraire l'ID client de l'ID du bouton cliqué
    client_id = triggered_button_id_dict.get('index')
    if not client_id:
        return dbc.Alert("Erreur : ID client non trouvé.", color="danger")

    # Trouver la valeur du dropdown correspondant à ce client_id
    selected_role = None
    for i, select_id_dict in enumerate(role_select_ids):
        # Vérifier si select_id_dict est bien un dictionnaire avant d'utiliser .get()
        if isinstance(select_id_dict, dict) and select_id_dict.get('index') == client_id:
            # Assurer que l'index est valide pour la liste des valeurs
            if i < len(role_select_values):
                 selected_role = role_select_values[i]
                 break # On a trouvé la valeur correspondante

    if client_id and selected_role:
        print(f"Tentative de mise à jour du rôle pour client ID {client_id} à '{selected_role}'")
        # Appeler la fonction de mise à jour en BDD
        update_success = update_client_role_in_db(client_id, selected_role)

        if update_success:
            # Afficher un message de succès
            # Note: Ceci remplacera la carte d'info utilisateur. Pour garder la carte et ajouter un message,
            # il faudrait une structure de sortie plus complexe ou un composant d'alerte séparé.
            return dbc.Alert(f"Le rôle du client ID {client_id} a été mis à jour à '{selected_role}'.", color="success", duration=4000, className="mt-3")
        else:
            # Afficher un message d'erreur
             return dbc.Alert(f"Erreur lors de la mise à jour du rôle pour le client ID {client_id}.", color="danger", className="mt-3")
    elif client_id and not selected_role:
         # Si le rôle n'est pas sélectionné dans le dropdown
         return dbc.Alert("Veuillez sélectionner un rôle avant d'enregistrer.", color="warning", className="mt-3")
    else:
        # Cas où client_id n'a pas pu être déterminé ou selected_role non trouvé
        return dbc.Alert("Erreur lors de la récupération des informations pour la mise à jour.", color="danger", className="mt-3")


# ==================================================================
# === CALLBACKS POUR LE MODAL DE CONFIRMATION DE SUPPRESSION (INCHANGÉS) ===
# ==================================================================
# ... (open_delete_confirmation_modal et handle_delete_confirmation inchangés) ...
@callback(
    Output("delete-client-confirmation-modal", "is_open"),
    Output("store-delete-target-client-id", "data"),
    Output("delete-client-modal-body", "children"),
    Input({"type": "delete-client-open-modal-btn", "index": ALL}, "n_clicks"),
    State({"type": "delete-client-open-modal-btn", "index": ALL}, "id"),
    prevent_initial_call=True
)
def open_delete_confirmation_modal(n_clicks, button_ids):
    # ... (code inchangé) ...
    ctx = callback_context
    if not ctx.triggered or not any(click for click in n_clicks if click):
        return no_update, no_update, no_update
    button_id_dict = ctx.triggered_id
    if button_id_dict and button_id_dict.get('type') == 'delete-client-open-modal-btn':
        client_id_to_delete = button_id_dict.get('index')
        modal_body_text = f"Êtes-vous sûr de vouloir supprimer le compte ID: {client_id_to_delete}? Cette action est irréversible."
        print(f"Ouverture du modal de suppression pour l'ID client : {client_id_to_delete}")
        return True, client_id_to_delete, modal_body_text
    else:
        return no_update, no_update, no_update

@callback(
    Output("delete-client-confirmation-modal", "is_open", allow_duplicate=True),
    Output("resultat-recherche", "children", allow_duplicate=True),
    Output("store-delete-target-client-id", "data", allow_duplicate=True),
    Input("confirm-delete-client-button", "n_clicks"),
    Input("cancel-delete-client-button", "n_clicks"),
    State("store-delete-target-client-id", "data"),
    prevent_initial_call=True
)
def handle_delete_confirmation(confirm_clicks, cancel_clicks, client_id_to_delete):
    # ... (code inchangé) ...
    triggered_id = callback_context.triggered_id
    if triggered_id == "confirm-delete-client-button" and client_id_to_delete:
        print(f"Confirmation de suppression reçue pour l'ID client : {client_id_to_delete}")
        delete_success = delete_client_by_id(client_id_to_delete)
        if delete_success:
            result_message = dbc.Alert(f"Le compte ID {client_id_to_delete} a été supprimé avec succès.", color="success", duration=5000, className="mt-3")
        else:
            result_message = dbc.Alert(f"Erreur lors de la suppression du compte ID {client_id_to_delete}. Consultez les logs.", color="danger", className="mt-3")
        # Vide la zone de résultat après suppression
        return False, result_message, None
    elif triggered_id == "cancel-delete-client-button":
        print("Annulation de la suppression.")
        return False, no_update, None
    else:
        return no_update, no_update, no_update