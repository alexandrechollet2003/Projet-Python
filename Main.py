import secrets
import string
import hashlib
import csv
from datetime import datetime, timedelta

# -------------------------------------------------------------
# 1) PARAMÈTRES & VARIABLES GLOBALES
# -------------------------------------------------------------

CSV_FILE = "users.csv"
users_db = []

VALID_SITES = ["paris", "marseille", "rennes", "grenoble"]
VALID_ROLES = ["SUPER_ADMIN", "ADMIN_REGION", "USER"]


# -------------------------------------------------------------
# 2) FONCTIONS DE SÉCURITÉ
# -------------------------------------------------------------

def generate_login(prenom: str, nom: str) -> str:
    """Génère login = initiale + nom (sans suffixe si possible)."""
    base = (prenom[0] + nom).lower()

    # Vérifie collision
    existing = {u["login"] for u in users_db}
    login = base

    i = 1
    while login in existing:
        login = f"{base}{i}"
        i += 1

    return login


def generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def password_validity(days: int = 90) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


# -------------------------------------------------------------
# 3) CSV : CHARGEMENT & SAUVEGARDE
# -------------------------------------------------------------

def load_users():
    """Charge le CSV en mémoire dans users_db."""
    global users_db
    users_db = []

    try:
        with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                users_db.append(dict(row))
    except FileNotFoundError:
        users_db = []


def save_users():
    """Sauvegarde complète en CSV."""
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "login", "prenom", "nom", "role", "site",
            "pwd_hash", "pwd_valid_until"
        ])
        writer.writeheader()
        writer.writerows(users_db)


# -------------------------------------------------------------
# 4) CRÉATION UTILISATEUR
# -------------------------------------------------------------

def get_valid_site():
    while True:
        site = input("Site (Paris / Marseille / Rennes / Grenoble) : ").strip().lower()
        if site in VALID_SITES:
            return site.capitalize()
        print("❌ Site invalide !")


def create_user_basic(prenom: str, nom: str, role: str, site: str) -> dict:
    login = generate_login(prenom, nom)
    return {
        "login": login,
        "prenom": prenom.capitalize(),
        "nom": nom.capitalize(),
        "role": role,
        "site": site,
        "pwd_hash": "",
        "pwd_valid_until": "",
    }


def secure_account(user: dict) -> str:
    password = generate_password()
    user["pwd_hash"] = hash_password(password)
    user["pwd_valid_until"] = password_validity()
    return password


def add_user(user: dict):
    users_db.append(user)
    save_users()


# -------------------------------------------------------------
# 5) UTILITAIRES / RECHERCHE
# -------------------------------------------------------------

def find_user_by_login(login: str) -> dict | None:
    return next((u for u in users_db if u["login"] == login), None)


def is_admin(user: dict) -> bool:
    return user["role"] in ("SUPER_ADMIN", "ADMIN_REGION")


def same_site(user: dict, other: dict) -> bool:
    return user["site"].lower() == other["site"].lower()


# -------------------------------------------------------------
# 6) CRUD UTILISATEURS (AVEC CONTRÔLE DES RÔLES)
# -------------------------------------------------------------

def afficher_tous(current_user: dict):
    print("\n===== LISTE DES UTILISATEURS =====")
    if not users_db:
        print("Aucun utilisateur créé.")
        return

    if current_user["role"] == "SUPER_ADMIN":
        to_show = users_db
    else:  # ADMIN_REGION
        to_show = [u for u in users_db if same_site(current_user, u)]

    for u in to_show:
        print(u)


def modifier_utilisateur(current_user: dict):
    if not users_db:
        print("Aucun utilisateur à modifier.")
        return

    login = input("Login de l'utilisateur à modifier : ").strip()
    user = find_user_by_login(login)

    if not user:
        print("❌ Utilisateur non trouvé.")
        return

    # Restrictions pour ADMIN_REGION
    if current_user["role"] == "ADMIN_REGION":
        if user["role"] == "SUPER_ADMIN":
            print("⛔ Vous ne pouvez pas modifier un SUPER_ADMIN.")
            return
        if not same_site(current_user, user):
            print("⛔ Vous ne pouvez modifier que les utilisateurs de votre site.")
            return

    print(f"\n--- Modification de {login} ---")

    new_prenom = input(f"Prénom ({user['prenom']}): ").strip()
    new_nom = input(f"Nom ({user['nom']}): ").strip()
    new_site = input(f"Site ({user['site']}): ").strip()
    new_role = input(f"Rôle ({user['role']}): ").strip()

    if new_prenom:
        user["prenom"] = new_prenom.capitalize()
    if new_nom:
        user["nom"] = new_nom.capitalize()
    if new_site:
        if new_site.lower() in VALID_SITES:
            # Si ADMIN_REGION, on interdit de changer vers un autre site
            if current_user["role"] == "ADMIN_REGION" and new_site.capitalize() != current_user["site"]:
                print("⚠ Site ignoré : vous ne pouvez pas changer vers une autre région.")
            else:
                user["site"] = new_site.capitalize()
        else:
            print("⚠ Site ignoré (invalide).")
    if new_role:
        new_role_up = new_role.upper()
        if new_role_up in VALID_ROLES:
            if current_user["role"] == "ADMIN_REGION" and new_role_up == "SUPER_ADMIN":
                print("⚠ Vous ne pouvez pas attribuer le rôle SUPER_ADMIN.")
            else:
                user["role"] = new_role_up
        else:
            print("⚠ Rôle ignoré (invalide).")

    save_users()
    print("✔ Modification faite.")


def supprimer_utilisateur(current_user: dict):
    if not users_db:
        print("Aucun utilisateur créé.")
        return

    login = input("Login à supprimer : ").strip()
    user = find_user_by_login(login)

    if not user:
        print("❌ Utilisateur non trouvé.")
        return

    # Restrictions pour ADMIN_REGION
    if current_user["role"] == "ADMIN_REGION":
        if user["role"] == "SUPER_ADMIN":
            print("⛔ Vous ne pouvez pas supprimer un SUPER_ADMIN.")
            return
        if not same_site(current_user, user):
            print("⛔ Vous ne pouvez supprimer que les utilisateurs de votre site.")
            return

    users_db.remove(user)
    save_users()
    print(f"✔ Utilisateur {login} supprimé avec succès.")


# -------------------------------------------------------------
# 7) FONCTIONS DE CRÉATION (AVEC CONTRÔLE DES RÔLES)
# -------------------------------------------------------------

def creer_admin(current_user: dict):
    if not is_admin(current_user):
        print("⛔ Accès refusé.")
        return

    print("\n--- Création d'un ADMIN ---")
    prenom = input("Prénom : ").strip()
    nom = input("Nom : ").strip()

    # Site & rôle selon le type d'admin connecté
    if current_user["role"] == "SUPER_ADMIN":
        site = get_valid_site()
        role = "ADMIN_REGION"
        if site.lower() == "paris":
            if input("Super admin ? (o/n) : ").strip().lower() == "o":
                role = "SUPER_ADMIN"
    else:  # ADMIN_REGION
        site = current_user["site"]
        role = "ADMIN_REGION"
        print(f"(Site forcé à votre région : {site})")

    user = create_user_basic(prenom, nom, role, site)
    pwd = secure_account(user)
    add_user(user)

    print(f"\n✔ Admin créé : {user['login']} ({role} - {site})")
    print(f"Mot de passe initial : {pwd}\n")


def creer_user(current_user: dict):
    if not is_admin(current_user):
        print("⛔ Accès refusé.")
        return

    print("\n--- Création d'un USER ---")
    prenom = input("Prénom : ").strip()
    nom = input("Nom : ").strip()

    if current_user["role"] == "SUPER_ADMIN":
        site = get_valid_site()
    else:  # ADMIN_REGION
        site = current_user["site"]
        print(f"(Site forcé à votre région : {site})")

    user = create_user_basic(prenom, nom, "USER", site)
    pwd = secure_account(user)
    add_user(user)

    print(f"\n✔ Utilisateur créé : {user['login']} (USER - {site})")
    print(f"Mot de passe : {pwd}\n")


# -------------------------------------------------------------
# 8) AUTHENTIFICATION
# -------------------------------------------------------------

def create_default_super_admin():
    """Création d'un SUPER_ADMIN par défaut si la base est vide."""
    print("⚠ Aucun utilisateur trouvé : création d'un SUPER_ADMIN par défaut.")
    default_user = {
        "login": "sadmin",
        "prenom": "Super",
        "nom": "Admin",
        "role": "SUPER_ADMIN",
        "site": "Paris",
        "pwd_hash": hash_password("admin123"),
        "pwd_valid_until": password_validity()
    }
    users_db.append(default_user)
    save_users()
    print("   Login : sadmin")
    print("   Mot de passe : admin123\n")


def login_screen() -> dict | None:
    """Affiche l'écran de login et renvoie l'utilisateur connecté ou None."""
    if not users_db:
        create_default_super_admin()

    print("\n🔐 ===== AUTHENTIFICATION =====")
    attempts = 3
    while attempts > 0:
        login = input("Login : ").strip()
        pwd = input("Mot de passe : ").strip()
        pwd_hash = hash_password(pwd)

        user = next(
            (u for u in users_db if u["login"] == login and u["pwd_hash"] == pwd_hash),
            None
        )

        if user:
            if not is_admin(user):
                print("⛔ Accès refusé : seuls les ADMIN et SUPER_ADMIN ont accès au menu.")
                return None

            print(f"\n✅ Connexion réussie. Bonjour {user['prenom']} "
                  f"({user['role']} - {user['site']}).")
            return user

        attempts -= 1
        print(f"❌ Identifiants incorrects. Tentatives restantes : {attempts}")

    print("⛔ Trop de tentatives. Fermeture.")
    return None


# -------------------------------------------------------------
# 9) MENU PRINCIPAL (APRÈS CONNEXION)
# -------------------------------------------------------------

def menu(current_user: dict):
    while True:
        print("\n===== MENU GESTION UTILISATEURS =====")
        print(f"Connecté en tant que : {current_user['login']} "
              f"({current_user['role']} - {current_user['site']})")
        print("1. Créer un ADMIN")
        print("2. Créer un USER")
        print("3. Afficher tous les utilisateurs")
        print("4. Modifier un utilisateur")
        print("5. Supprimer un utilisateur")
        print("6. Déconnexion")

        choix = input("Votre choix : ")

        if choix == "1":
            creer_admin(current_user)
        elif choix == "2":
            creer_user(current_user)
        elif choix == "3":
            afficher_tous(current_user)
        elif choix == "4":
            modifier_utilisateur(current_user)
        elif choix == "5":
            supprimer_utilisateur(current_user)
        elif choix == "6":
            print("🔓 Déconnexion en cours...\n")
            return
        else:
            print("❌ Choix invalide.")


# -------------------------------------------------------------
# 10) LANCEMENT
# -------------------------------------------------------------

if __name__ == "__main__":
    load_users()
    while True:
        current_user = login_screen()
        if not current_user:
            print("Fermeture du programme.")
            break
        menu(current_user)
