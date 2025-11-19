import csv
import hashlib
import secrets
from datetime import datetime, timedelta

# --- CONFIGURATION ---
FICHIER_DB = "utilisateurs.csv"
DUREE_VALIDITE_JOURS = 90

# --- RÈGLES DE GESTION & SÉCURITÉ ---

def generer_login(prenom, nom):
    """Règle : 1ère lettre prénom + nom (tout minuscule, sans espace)."""
    if not prenom or not nom: return "inconnu"
    nom_clean = nom.replace(" ", "").lower()
    prenom_clean = prenom.replace(" ", "").lower()
    return f"{prenom_clean[0]}{nom_clean}"

def generer_mot_de_passe(longueur=10):
    """Règle : Génération aléatoire (Lettres + Chiffres)."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longueur))

def hacher_pwd(mot_de_passe):
    """Règle : Hashage SHA256 avant stockage/vérification."""
    return hashlib.sha256(mot_de_passe.encode()).hexdigest()

def calculer_expiration():
    return (datetime.now() + timedelta(days=DUREE_VALIDITE_JOURS)).strftime("%Y-%m-%d")

# --- GESTION DES FICHIERS (CSV) ---

def charger_donnees():
    users = []
    if os.path.exists(FICHIER_DB):
        with open(FICHIER_DB, mode='r', newline='', encoding='utf-8') as f:
            try:
                reader = csv.DictReader(f)
                users = list(reader)
            except csv.Error:
                users = []
    return users

def sauvegarder_donnees(users):
    with open(FICHIER_DB, mode='w', newline='', encoding='utf-8') as f:
        champs = ["login", "prenom", "nom", "role", "pwd_hash", "date_validite"]
        writer = csv.DictWriter(f, fieldnames=champs)
        writer.writeheader()
        writer.writerows(users)

# --- FONCTIONNALITÉS MÉTIER ---

def ajouter_utilisateur(users):
    print("\n--- [CRÉATION UTILISATEUR] ---")
    prenom = input("Prénom : ").strip()
    nom = input("Nom : ").strip()
    role = input("Rôle (admin/patient) : ").strip().lower()

    login = generer_login(prenom, nom)
    pwd_clair = generer_mot_de_passe()
    pwd_hash = hacher_pwd(pwd_clair)
    validite = calculer_expiration()

    # Vérification doublon
    for u in users:
        if u['login'] == login:
            print(f"⚠ Erreur : Le login '{login}' existe déjà.")
            return

    nouvel_user = {
        "login": login,
        "prenom": prenom,
        "nom": nom,
        "role": role,
        "pwd_hash": pwd_hash,
        "date_validite": validite
    }
    
    users.append(nouvel_user)
    sauvegarder_donnees(users)
    
    print(f"✅ Utilisateur créé avec succès !")
    print(f"   -> Login : {login}")
    print(f"   -> Mot de passe : {pwd_clair}")

def lister_utilisateurs(users):
    print("\n--- [LISTE DES UTILISATEURS] ---")
    print(f"{'LOGIN':<15} | {'NOM COMPLET':<20} | {'ROLE':<10}")
    print("-" * 50)
    for u in users:
        nom_complet = f"{u['prenom']} {u['nom']}"
        print(f"{u['login']:<15} | {nom_complet:<20} | {u['role']:<10}")
    print("-" * 50)

def rechercher_utilisateur(users):
    cible = input("\nLogin ou nom à chercher : ").lower()
    trouve = False
    for u in users:
        if cible in u['login'] or cible in u['nom'].lower():
            print(f"-> Trouvé : {u['prenom']} {u['nom']} (Role: {u['role']})")
            trouve = True
    if not trouve: print("Introuvable.")

def modifier_supprimer(users):
    login_cible = input("\nLogin de l'utilisateur cible : ")
    index = next((i for i, u in enumerate(users) if u['login'] == login_cible), -1)
    
    if index == -1:
        print("Utilisateur introuvable.")
        return

    action = input("Action : (S)upprimer / (M)odifier rôle ? ").upper()
    if action == 'S':
        if input("Confirmer (o/n) ? ") == 'o':
            del users[index]
            sauvegarder_donnees(users)
            print("Supprimé.")
    elif action == 'M':
        users[index]['role'] = input("Nouveau rôle : ")
        sauvegarder_donnees(users)
        print("Modifié.")

# --- SYSTÈME DE LOGIN ---

def creer_admin_par_defaut(users):
    """Crée un admin de secours si la base est vide."""
    print("⚠ Base vide : Création d'un administrateur par défaut.")
    login = "sadmin"
    pwd_clair = "admin123" # Mot de passe par défaut
    pwd_hash = hacher_pwd(pwd_clair)
    
    admin_defaut = {
        "login": login,
        "prenom": "Super",
        "nom": "Admin",
        "role": "admin",
        "pwd_hash": pwd_hash,
        "date_validite": calculer_expiration()
    }
    users.append(admin_defaut)
    sauvegarder_donnees(users)
    print(f"-> Login : {login}")
    print(f"-> Pass  : {pwd_clair}")
    print("Veuillez vous connecter avec ces identifiants.\n")

def ecran_connexion(users):
    """Gère l'authentification au lancement."""
    print("\n🔐 === AUTHENTIFICATION REQUISE ===")
    
    tentatives = 3
    while tentatives > 0:
        login_input = input("Login : ")
        pwd_input = input("Mot de passe : ")
        hash_input = hacher_pwd(pwd_input)
        
        for user in users:
            if user['login'] == login_input and user['pwd_hash'] == hash_input:
                # Vérification des droits
                if user['role'] == 'admin':
                    print(f"\nBienvenue {user['prenom']}.")
                    return True
                else:
                    print("⛔ Accès refusé : Seuls les admins peuvent accéder à ce menu.")
                    return False
        
        print("❌ Identifiants incorrects.")
        tentatives -= 1
        print(f"Il reste {tentatives} tentative(s).")
    
    return False

# --- PROGRAMME PRINCIPAL ---

def main():
    db_users = charger_donnees()

    # 1. Si base vide -> Création admin secours
    if not db_users:
        creer_admin_par_defaut(db_users)
        db_users = charger_donnees() # Recharger pour inclure le nouvel admin

    # 2. Écran de connexion
    acces_autorise = ecran_connexion(db_users)

    # 3. Si connecté -> Menu Gestion
    if acces_autorise:
        while True:
            print("\n--- MENU ADMIN ---")
            print("1. Créer Utilisateur")
            print("2. Liste Utilisateurs")
            print("3. Rechercher")
            print("4. Modifier/Supprimer")
            print("5. Quitter")
            
            choix = input("Choix : ")
            if choix == '1': ajouter_utilisateur(db_users)
            elif choix == '2': lister_utilisateurs(db_users)
            elif choix == '3': rechercher_utilisateur(db_users)
            elif choix == '4': modifier_supprimer(db_users)
            elif choix == '5': break
    else:
        print("Fermeture du programme.")

if __name__ == "__main__":
    main()