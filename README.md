# GUDLFT — Réservations des compétitions

Application web légère (Proof of Concept) développée avec **Flask**, permettant aux secrétaires de clubs d'inscrire leurs athlètes aux compétitions régionales en utilisant leur solde de points, et d'afficher publiquement le classement des points des clubs.

---

## 1. Objectif du projet

Cette application remplace les inscriptions manuelles par un portail réservé aux secrétaires de clubs :
- **Connexion par adresse e-mail** de secrétaire de club et consultation du calendrier des compétitions.
- **Réservation de places** contre des points (`1 point = 1 place`), dans la limite de **12 places maximum par club et par compétition** (réservations cumulées), du solde de points du club et des places restantes.
- **Interdiction de réserver** une compétition passée ou complète, et validation stricte des saisies (entier strictement positif).
- **Tableau public des points (`/points`)** accessible en lecture seule sans connexion, trié par ordre décroissant de points.

---

## 2. Prérequis et technologies

- **Python 3.11+**
- **Flask** — Micro-framework web
- **pytest**, **pytest-flask**, **pytest-cov**, **coverage** — Tests automatisés et mesure de couverture
- **flake8**, **flake8-html** — Vérification PEP 8 et génération du rapport qualité HTML
- **Locust** — Tests de charge et de performance

---

## 3. Installation et lancement sous Windows (PowerShell)

1. **Cloner le dépôt et se placer dans le dossier du projet** :
   ```powershell
   git clone https://github.com/davynanekpadro487-web/Python_Testing_2627.git
   cd Python_Testing_2627
   ```

2. **Créer et activer l'environnement virtuel** :
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(Sur macOS / Linux : `python3 -m venv venv && source venv/bin/activate`)*

3. **Installer les dépendances** :
   ```powershell
   pip install -r requirements.txt
   ```

4. **Lancer l'application Flask** :
   ```powershell
   $env:FLASK_APP = "server.py"
   flask run
   ```
   L'application est accessible sur `http://127.0.0.1:5000`.

### Comptes de démonstration (`clubs.json`)
- **Simply Lift** : `john@simplylift.co` (13 points)
- **She Lifts** : `kate@shelifts.co.uk` (12 points)
- **Iron Temple** : `admin@irontemple.com` (4 points)

---

## 4. Organisation des tests et commandes

Les tests sont répartis dans le dossier `tests/` selon la pyramide des tests :
- `tests/unit/` — **40 tests unitaires** : testent isolément chaque route, chaque règle métier, le filtre `date_fr` et le rendu de l'interface avec des données simulées via `tests/conftest.py`.
- `tests/integration/` — **8 tests d'intégration** (`test_booking_flow.py`) : vérifient l'enchaînement de plusieurs routes et la cohérence de l'état en mémoire.
- `tests/functional/` — **5 tests fonctionnels** (`test_user_journeys.py`) : simulent des parcours utilisateurs complets de bout en bout avec le client de test Flask.
- `tests/performance/` — **Tests de performance Locust** (`locustfile.py`).

### Exécuter tous les tests
```powershell
.\venv\Scripts\Activate.ps1
pytest
```

### Mesurer la couverture de code et générer le rapport HTML
```powershell
.\venv\Scripts\Activate.ps1
pytest --cov=server --cov-report=term-missing --cov-report=html:reports/coverage
```
- **Rapport de couverture HTML** : `reports/coverage/index.html`

---

## 5. Qualité du code (Flake8)

La configuration est définie dans `.flake8` (`max-line-length = 120`, exclusion de `venv,.git,__pycache__,reports`).

```powershell
.\venv\Scripts\Activate.ps1
flake8
flake8 --format=html --htmldir=reports/flake8
```
- **Rapport Flake8 HTML** : `reports/flake8/index.html`

---

## 6. Tests de performance (Locust)

Conformément aux spécifications fonctionnelles :
- **Charge simulée** : **6 utilisateurs simultanés**.
- **Temps de chargement de la liste des compétitions** (`/showSummary`) : **< 5 secondes**.
- **Temps de mise à jour des points** (`/purchasePlaces`) : **< 2 secondes**.

1. Dans un premier terminal, lancer le serveur Flask :
   ```powershell
   .\venv\Scripts\Activate.ps1
   $env:FLASK_APP = "server.py"
   flask run
   ```
2. Dans un second terminal, exécuter la campagne Locust (60 secondes) :
   ```powershell
   .\venv\Scripts\Activate.ps1
   locust -f tests/performance/locustfile.py --headless -u 6 -r 6 -t 60s --host http://127.0.0.1:5000 --html reports/locust_report.html --csv reports/locust
   ```
- **Rapports générés dans `reports/`** :
  - `reports/locust_report.html`
  - `reports/locust_stats.csv`
  - `reports/locust_stats_history.csv`
  - `reports/locust_failures.csv`
  - `reports/locust_exceptions.csv`

---

## 7. Conventions de nommage des branches

- `main` : branche principale contenant uniquement du code testé et fonctionnel.
- `bug/<nom-descriptif>` : correction d'un bogue identifié en Phase 1.
- `feature/<nom-descriptif>` : ajout d'une nouvelle fonctionnalité (tableau des points, traduction française, interface graphique).
- `amelioration/<nom-descriptif>` : amélioration de la suite de tests, de la performance et de la qualité du code.
- `QA` : branche de revue finale créée depuis `main` (non fusionnée dans `main`).

---

## 8. Limites connues

- **Absence de session d'authentification** : conformément à l'architecture du POC d'origine, aucune session utilisateur (`flask.session`) n'est ouverte à la connexion ; l'identité du club est transmise dans l'URL (`/book/<competition>/<club>`) et dans les champs cachés du formulaire de réservation (`/purchasePlaces`).
- **Persistance en mémoire uniquement** : les fichiers `clubs.json` et `competitions.json` sont chargés en mémoire au démarrage du serveur sans écriture sur disque. Les réservations et les soldes de points sont donc réinitialisés à chaque redémarrage de l'application.
