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
    """Charge le CSV."""
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
# 5) CRUD UTILISATEURS
# -------------------------------------------------------------

def afficher_tous():
    print("\n===== LISTE DES UTILISATEURS =====")
    if not users_db:
        print("Aucun utilisateur créé.")
        return

    for u in users_db:
        print(u)


def modifier_utilisateur():
    if not users_db:
        print("Aucun utilisateur à modifier.")
        return

    login = input("Login de l'utilisateur à modifier : ").strip()
    user = next((u for u in users_db if u["login"] == login), None)

    if not user:
        print("❌ Utilisateur non trouvé.")
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
            user["site"] = new_site.capitalize()
        else:
            print("⚠ Site ignoré (invalide).")
    if new_role:
        if new_role.upper() in VALID_ROLES:
            user["role"] = new_role.upper()
        else:
            print("⚠ Rôle ignoré (invalide).")

    save_users()
    print("✔ Modification faite.")


def supprimer_utilisateur():
    if not users_db:
        print("Aucun utilisateur créé.")
        return

    login = input("Login à supprimer : ").strip()
    user = next((u for u in users_db if u["login"] == login), None)

    if not user:
        print("❌ Utilisateur non trouvé.")
        return

    users_db.remove(user)
    save_users()
    print(f"✔ Utilisateur {login} supprimé avec succès.")


# -------------------------------------------------------------
# 6) FONCTIONS DU MENU
# -------------------------------------------------------------

def creer_admin():
    print("\n--- Création d'un ADMIN ---")
    prenom = input("Prénom : ").strip()
    nom = input("Nom : ").strip()
    site = get_valid_site()

    role = "ADMIN_REGION"
    if site.lower() == "paris":
        if input("Super admin ? (o/n) : ").strip().lower() == "o":
            role = "SUPER_ADMIN"

    user = create_user_basic(prenom, nom, role, site)
    pwd = secure_account(user)
    add_user(user)

    print(f"\n✔ Admin créé : {user['login']} ({role})")
    print(f"Mot de passe initial : {pwd}\n")


def creer_user():
    print("\n--- Création d'un USER ---")
    prenom = input("Prénom : ").strip()
    nom = input("Nom : ").strip()
    site = get_valid_site()

    user = create_user_basic(prenom, nom, "USER", site)
    pwd = secure_account(user)
    add_user(user)

    print(f"\n✔ Utilisateur créé : {user['login']} (USER - {site})")
    print(f"Mot de passe : {pwd}\n")


# -------------------------------------------------------------
# 7) MENU PRINCIPAL
# -------------------------------------------------------------

def menu():
    while True:
        print("\n===== MENU GESTION UTILISATEURS =====")
        print("1. Créer un ADMIN")
        print("2. Créer un USER")
        print("3. Afficher tous les utilisateurs")
        print("4. Modifier un utilisateur")
        print("5. Supprimer un utilisateur")
        print("6. Quitter")

        choix = input("Votre choix : ")

        if choix == "1":
            creer_admin()
        elif choix == "2":
            creer_user()
        elif choix == "3":
            afficher_tous()
        elif choix == "4":
            modifier_utilisateur()
        elif choix == "5":
            supprimer_utilisateur()
        elif choix == "6":
            print("Fermeture du programme.")
            break
        else:
            print("❌ Choix invalide.")


# -------------------------------------------------------------
# 8) LANCEMENT
# -------------------------------------------------------------

if __name__ == "__main__":
    load_users()
    menu()
