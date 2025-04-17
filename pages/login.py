import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State, no_update

# Enregistrement de la page (INCHANGÉ)
dash.register_page(__name__, path='/login')

# --- Layout Principal ---
def layout():

    # --- Formulaire de Connexion (Basé sur votre version html.Form qui fonctionnait) ---
    login_form = dbc.Card( # Envelopper dans une carte pour le style d'onglet
        dbc.CardBody([
             html.Form(
                [
                    # Pas besoin de titre ici, il est dans l'onglet
                    # html.H2("Connexion à Ciracbot", className="text-center mb-4"),

                    # Champ Email
                    html.Div([
                        dbc.Label("Adresse Email", html_for="login-email"),
                        dcc.Input(
                            type="email", id="login-email", name="email",
                            placeholder="votre.email@example.com", required=True,
                            className="form-control mb-3"
                        ),
                    ]),

                    # Champ Mot de Passe
                    html.Div([
                        dbc.Label("Mot de passe", html_for="login-password"),
                        dcc.Input(
                            type="password", id="login-password", name="password",
                            placeholder="Votre mot de passe", required=True,
                            className="form-control mb-3"
                        ),
                    ]),

                    # Bouton de Connexion
                    html.Button(
                        "Se connecter", id="login-submit-button", type="submit",
                        className="btn btn-primary w-100"
                    ),

                    # Zone Flash pour les erreurs de connexion
                    html.Div(id="login-flash-output", className="mt-3 text-center"), # Garder l'ID
                ],
                method='POST',
                action='/login' # Action pointe vers la route de connexion Flask
             )
        ])
    )

    # --- Formulaire d'Inscription (Nouveau) ---
    register_form = dbc.Card( # Envelopper dans une carte
        dbc.CardBody([
            html.Form(
                [
                    # Titre spécifique à l'inscription (optionnel)
                    # html.H4("Nouveau Compte", className="text-center mb-4"),

                    dbc.Row([ # Utiliser Row/Col pour la mise en page
                        dbc.Col([
                            dbc.Label("Prénom", html_for="register-first-name"),
                            dcc.Input(
                                type="text", id="register-first-name", name="first_name",
                                placeholder="Votre prénom", required=True,
                                className="form-control mb-3"
                            ),
                        ], md=6),
                        dbc.Col([
                             dbc.Label("Nom", html_for="register-last-name"),
                             dcc.Input(
                                type="text", id="register-last-name", name="last_name",
                                placeholder="Votre nom", required=True,
                                className="form-control mb-3"
                            ),
                        ], md=6),
                    ]),

                     dbc.Row([
                        dbc.Col([
                            dbc.Label("Adresse Email", html_for="register-email"),
                             dcc.Input(
                                type="email", id="register-email", name="email",
                                placeholder="votre.email@example.com", required=True,
                                className="form-control mb-3"
                             ),
                        ], md=6),
                         dbc.Col([
                             dbc.Label("Age", html_for="register-age"),
                             dcc.Input(
                                type="number", id="register-age", name="age",
                                placeholder="Votre âge", required=False, # Rendre optionnel si besoin
                                min=0, # Age ne peut pas être négatif
                                className="form-control mb-3"
                            ),
                        ], md=6),
                    ]),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Mot de passe", html_for="register-password"),
                             dcc.Input(
                                type="password", id="register-password", name="password",
                                placeholder="Choisissez un mot de passe", required=True,
                                className="form-control mb-3"
                             ),
                        ], md=6),
                         dbc.Col([
                            dbc.Label("Confirmer le mot de passe", html_for="register-confirm-password"),
                             dcc.Input(
                                type="password", id="register-confirm-password", name="confirm_password",
                                placeholder="Confirmez le mot de passe", required=True,
                                className="form-control mb-3"
                             ),
                        ], md=6),
                    ]),

                    # Bouton d'Inscription
                    html.Button(
                        "Créer mon compte", id="register-submit-button", type="submit",
                        className="btn btn-success w-100" # Couleur différente
                    ),

                    # Zone pour les messages d'erreur/succès d'inscription
                    html.Div(id="register-feedback-output", className="mt-3 text-center"),

                ],
                method='POST',
                action='/register' # IMPORTANT: Action pointe vers une NOUVELLE route Flask
            )
        ])
    )

    # --- Structure Principale avec Onglets ---
    return dbc.Container(
        dbc.Row(
            dbc.Col(
                [
                    html.H2("Accès à Ciracbot", className="text-center my-4"),
                    dbc.Tabs(
                        [
                            dbc.Tab(login_form, label="Se Connecter", tab_id="tab-login"),
                            dbc.Tab(register_form, label="Créer un Compte", tab_id="tab-register"),
                        ],
                        id="login-register-tabs",
                        active_tab="tab-login", # Onglet de connexion actif par défaut
                    ),
                ],
                width=12, lg=8, md=10 # Ajuster la largeur globale
            ),
            justify="center",
            className="mt-4 mb-5"
        ),
        fluid=False
    )