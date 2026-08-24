# Bloc par issue : exemple complet

Exemple rempli montrant à quoi ressemble un bloc de fonctionnalité par issue. Sers-t'en pour le
**niveau de précision attendu** — ne le copie pas mot pour mot.

> ⚠️ **Cet exemple porte sur une application web multi-comptes avec upload et traitement
> asynchrone.** C'est un archétype parmi d'autres, pas le modèle à reproduire. Les sous-sections
> d'un vrai bloc sont celles des **surfaces déclarées dans `.claude/pipeline.config.md`** : sur une
> CLI, « Vérifications Frontend » n'existe pas ; sur une bibliothèque, ni persistance ni worker. Ce
> qu'il faut retenir, c'est la **granularité** — routes réelles, codes réels, champs réels — pas la
> liste des sections.

L'exemple porte sur une issue hypothétique `#127 — L'upload de document de connaissance accepte le PDF et rejette les fichiers trop volumineux`, qui était la deuxième issue dérivée de `PRD #100 — Base de connaissances client v2`.

---

## Bloc de fonctionnalité : Issue #127 — L'upload de document de connaissance accepte le PDF et rejette les fichiers trop volumineux

**Source** : #127 | PRD #100 | commits de livraison : `a1b2c3d`, `e4f5g6h`

**Objectif** : Un utilisateur connecté peut uploader un PDF jusqu'à 25 Mo dans la base de connaissances de son client. Les fichiers de plus de 25 Mo ou dont les magic bytes ne correspondent pas sont rejetés avant qu'aucune ligne BDD ou objet de stockage ne soit créé.

**Critères d'acceptation** (depuis #127) :
- [ ] Uploader un PDF valide de 1 Mo en tant qu'utilisateur A → succès, le document apparaît dans la liste de connaissances.
- [ ] Uploader un PDF de 30 Mo → rejet avec la taille dans le message d'erreur.
- [ ] Uploader un fichier `.pdf` dont le contenu réel est un PNG → rejet avec une erreur de magic bytes.
- [ ] L'utilisateur B ne peut pas voir le document uploadé par l'utilisateur A.

**Vérifications Backend / API** :
- [ ] `POST /api/clients/$CLIENT_A_ID/knowledge` avec `fixtures/valid-1mb.pdf` et `$TOKEN_A` → 201, le corps a `id`, `original_filename`, `status: "pending_extraction"`.
- [ ] `POST /api/clients/$CLIENT_A_ID/knowledge` avec `fixtures/oversized-30mb.pdf` et `$TOKEN_A` → 413, le corps a `error: "FILE_TOO_LARGE"`, `max_bytes: 26214400`.
- [ ] `POST /api/clients/$CLIENT_A_ID/knowledge` avec `fixtures/png-renamed-as-pdf.pdf` et `$TOKEN_A` → 422, le corps a `error: "INVALID_MAGIC_BYTES"`.
- [ ] `GET /api/clients/$CLIENT_A_ID/knowledge` avec `$TOKEN_B` → 403 (inter-locataires).
- [ ] `GET /api/clients/$CLIENT_A_ID/knowledge/<doc-id>` avec `$TOKEN_B` → 403 ou 404 selon la politique anti-énumération (décision projet : 404).
- [ ] Aucun appel `POST /api/clients/<id>/knowledge` ne retourne 500 pour les cas d'échec de validation.

**Vérifications Frontend** :
- [ ] URL : `https://app.local/clients/<client-a>/knowledge` depuis l'utilisateur A.
- [ ] L'état vide de connaissances affiche le CTA « Uploadez votre premier document » lorsque l'utilisateur A n'a aucun document.
- [ ] Pendant l'upload, le bouton d'upload est désactivé et un spinner est visible.
- [ ] À l'upload valide, la ligne du document apparaît avec `status: pending_extraction`, puis passe à `ready` une fois le polling terminé.
- [ ] À l'upload de 30 Mo, l'erreur visible affiche « Le fichier dépasse 25 Mo » (détail backend remonté, pas « Une erreur est survenue »).
- [ ] À l'échec de magic bytes, l'erreur visible affiche « Le contenu du fichier ne correspond pas à son extension ».
- [ ] Le polling s'arrête une fois le statut `ready` ou `failed` (aucun intervalle qui fuit après la terminalisation de la ligne).
- [ ] La console du navigateur n'a aucune erreur inexpliquée pendant les trois tentatives d'upload.
- [ ] Onglet Réseau : aucun 500, aucune requête émise après un statut terminal.

**Vérifications BDD / stockage** :
- [ ] `select id, client_id, status, error, finished_at from knowledge_documents where client_id = '$CLIENT_A_ID'` montre une ligne avec `status='ready'` (ou transitoirement `pending_extraction` pendant le polling) et `error IS NULL`.
- [ ] Aucune ligne n'existe pour la tentative rejetée de 30 Mo ni pour la tentative de magic bytes (`select count(*) ... where original_filename like '%oversized%' or '%png-renamed%'` → 0).
- [ ] Le fichier original est présent à `storage/clients/$CLIENT_A_ID/knowledge/<doc-id>/original.pdf` avec la taille attendue.
- [ ] Aucun objet de stockage n'existe sous `storage/clients/$CLIENT_A_ID/knowledge/` pour les tentatives rejetées.

**Vérifications Worker / logs** :
- [ ] `docker compose logs --tail=200 api` pour la fenêtre du run montre deux lignes de log `knowledge_upload_rejected` (une pour la taille, une pour les magic bytes), aucune trace d'exception.
- [ ] `docker compose logs --tail=200 worker` montre le job d'extraction du PDF valide passant de `started → completed`.
- [ ] Aucune ligne `Unhandled exception` dans l'un ou l'autre flux.

**Règle d'arrêt** : Un 500 sur tout upload rejeté, ou une ligne créée pour un upload rejeté, est **bloquant** — déposer via `bug-vers-issue` et ne pas continuer les blocs de fonctionnalité qui dépendent de la bonne isolation des documents de connaissance.

**Indices de sévérité** :
- Visibilité inter-locataires d'un document de connaissance → bloquant.
- Upload rejeté qui crée une ligne BDD ou un objet de stockage → bloquant.
- Erreur UI générique remplaçant le détail backend → majeur.
- Polling qui ne s'arrête pas à l'état terminal → majeur.
- Différences de formulation dans le message d'erreur → mineur.

---

## Ce que cet exemple illustre

- Chaque critère d'acceptation de l'issue est mappé à au moins une vérification explicite.
- Chaque vérification backend épingle la route, le code de statut et un champ de corps spécifique.
- Les vérifications frontend couvrent les états vide, chargement, succès, erreur — plus le comportement de polling — et s'ancrent à une vraie URL.
- Les vérifications BDD et stockage incluent la vraie table et la vraie disposition des chemins (vérifiée contre le diff).
- Les vérifications worker / logs bornent la queue de logs et nomment la ligne de log attendue.
- Les indices de sévérité préparent l'utilisateur aux décisions de triage avant qu'elles n'arrivent, pour que les défaillances pendant l'exécution soient rapides à classifier.
