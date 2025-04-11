import dash_bootstrap_components as dbc
from dash import html

def Navbar(user): # Accepte l'objet 'user' (current_user) depuis app.py
    # Déterminer l'état de l'utilisateur
    is_authenticated = user and user.is_authenticated
    is_admin = is_authenticated and hasattr(user, 'role') and user.role == 'admin'

    # --- Construction des éléments de navigation principaux (gauche/centre) ---
    # On commence avec les liens TOUJOURS visibles
    nav_items = [
        dbc.NavItem(dbc.NavLink("Accueil", href="/")),
    ]

    # Ajouter les liens pour TOUS les utilisateurs connectés
    if is_authenticated:
        # Ajouter les liens "Réclamations" et "Paramètres" ici
        nav_items.extend([
            dbc.NavItem(dbc.NavLink("Réclamations", href="/reclamations")),
            dbc.NavItem(dbc.NavLink("Paramètres", href="/parametres")),
        ])
        # Ajouter CONDITIONNELLEMENT le lien "Agent" si l'utilisateur est admin
        if is_admin:
            nav_items.append(dbc.NavItem(dbc.NavLink("Agent", href="/agent")))

    # --- Construction des éléments de droite (Connexion/Déconnexion/Nom) ---
    right_elements = []
    if is_authenticated:
        # Si connecté, afficher le nom (si disponible) et Déconnexion
        username_display = user.username if hasattr(user, 'username') else user.email
        right_elements.extend([
            # Optionnel : Afficher le nom de l'utilisateur
            # dbc.NavItem(dbc.NavLink(f"{username_display}", disabled=True, style={'color': 'rgba(255,255,255,.75)'})),
            html.A("Déconnexion", href="/logout", className="nav-link")
        ])
    else:
        # Si non connecté, afficher le lien Se connecter
        right_elements.append(
            dbc.NavItem(dbc.NavLink("Se connecter", href="/login"))
        )

    # --- Assemblage final de la Navbar ---
    navbar_component = dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("CIRACbot", href="/"),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Collapse(
                    dbc.Nav(nav_items, className="me-auto", navbar=True), # Liens principaux
                    id="navbar-collapse",
                    navbar=True,
                    is_open=False,
                ),
                dbc.Nav(right_elements, className="ms-auto", navbar=True), # Éléments à droite
            ], fluid=True
        ),
        color="dark",
        dark=True,
        sticky="top",
    )

    return navbar_component