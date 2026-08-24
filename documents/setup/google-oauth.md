# Mise en place du SSO Google

À faire **avant** de coder le domaine *Compte & identité*. Sans les identifiants ci-dessous,
l'écran Connexion (spec UX §4) ne peut ni être développé ni testé.

Référence produit : cadrage §12.1 (authentification), §12.2 (suppression de compte).

---

## Le piège à connaître avant de commencer

**Il faut DEUX identifiants clients, pas un.** C'est l'erreur qui coûte le plus de temps sur
Android :

| Client | Rôle | Qui s'en sert |
|---|---|---|
| **Android** | Autorise l'app signée à lancer le flux de connexion | Le SDK Google sur le téléphone |
| **Web** | Détermine le `aud` du jeton d'identité, donc ce que le backend vérifie | `serverClientId` côté app **et** l'api FastAPI |

L'app est Android, mais **c'est le client Web que le backend valide**. Créer uniquement le client
Android donne un jeton que le serveur refusera, avec un message qui ne dit pas pourquoi.

---

## 1. Projet Google Cloud

1. Ouvrir <https://console.cloud.google.com/> → **Nouveau projet** → nom `Arpendo`.
2. Menu **API et services** → **Écran de consentement OAuth**.
3. Type **Externe**. Renseigner : nom de l'app `Arpendo`, e-mail d'assistance, e-mail du
   développeur.
4. **Champs d'application** : ajouter `openid`, `.../auth/userinfo.email`,
   `.../auth/userinfo.profile`. **Rien d'autre.** Chaque champ supplémentaire est une donnée
   personnelle de plus à justifier au RGPD (cadrage §12.3) et rallonge la validation Google.
5. **Utilisateurs test** : ajouter ton compte. Tant que l'app n'est pas publiée, seuls ces
   comptes peuvent se connecter.

## 2. Empreinte SHA-1 de la clé de debug

Nécessaire pour créer le client Android. Depuis la racine du projet :

```
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

Relever la ligne `SHA1:`. Cette clé est générée par Android Studio et **n'est pas un secret** —
elle est identique sur toutes les machines de dev, ce qui est justement le problème qu'elle
n'a pas à résoudre.

## 3. Les deux clients

**API et services → Identifiants → Créer des identifiants → ID client OAuth.**

**a. Client Android**
- Type : *Android*
- Nom du package : `com.arpendo.game`
- Empreinte SHA-1 : celle de l'étape 2

**b. Client Web**
- Type : *Application Web*
- Nom : `Arpendo — backend`
- Aucune URI de redirection n'est nécessaire : le backend ne fait que **vérifier** un jeton,
  il n'exécute pas de flux de redirection.

## 4. Reporter dans `.env`

```
GOOGLE_ANDROID_CLIENT_ID=<client Android>.apps.googleusercontent.com
GOOGLE_WEB_CLIENT_ID=<client Web>.apps.googleusercontent.com
```

## 5. Ce que le backend doit vérifier

À l'implémentation, l'api valide le jeton d'identité Google en contrôlant **quatre** choses.
En omettre une transforme l'authentification en décoration :

1. **Signature** contre les clés publiques JWKS de Google, mises en cache avec un TTL
   (cadrage §13.0 — « JWKS en cache local »).
2. **`aud`** égal à `GOOGLE_WEB_CLIENT_ID`. Sans ce contrôle, un jeton émis pour **n'importe
   quelle autre application Google** est accepté.
3. **`iss`** égal à `https://accounts.google.com` ou `accounts.google.com`.
4. **`exp`** non dépassé.

---

## Avant la publication

⚠️ **Play App Signing re-signe l'application** (cadrage §13.11). L'APK livré aux joueurs n'est
donc **pas** signé avec ta clé, et l'empreinte SHA-1 de l'étape 2 ne correspondra plus.

Il faut, avant la première publication : récupérer l'empreinte SHA-1 du certificat de signature
d'application dans **Play Console → Configuration → Intégrité de l'application**, et l'ajouter
comme **seconde empreinte** au client Android. Oublier cette étape donne une app où la connexion
marche en debug et échoue chez tous les testeurs.

Rappel du cadrage §13.10 : **2FA obligatoire** sur le compte Google Cloud comme sur la Play
Console, et codes de récupération stockés hors ligne.
