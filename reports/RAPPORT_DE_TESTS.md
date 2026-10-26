# Rapport de Tests — Projet GUDLFT (`Python_Testing_2627`)

## 1. Introduction

### 1.1. Objectif
Ce rapport présente la stratégie de test, les corrections de bogues de la **Phase 1**, le développement des fonctionnalités de la **Phase 2** (tableau public des points des clubs), la refonte de l'interface en français ainsi que la couverture de code de l'application **GUDLFT — Réservations des compétitions**.

Conformément aux [Spécifications fonctionnelles](../Spécifications+fonctionnelles.pdf) et au brief initial du `README.md` :
> *« Vous devez tester de manière approfondie les résultats requis (à la fois les happy paths et les sad paths) pour toutes les fonctionnalités de l'application. Je vous encourage également à adopter une approche de TDD, car cela vous aidera à rationaliser votre travail. »*

### 1.2. Outils utilisés
- **`pytest` (v9.1.1)** & **`pytest-flask` (v1.3.0)** : exécution automatisée des tests unitaires, d'intégration et fonctionnels via le client de test Flask (`app.test_client()`).
- **`coverage` (v7.16.2)** & **`pytest-cov` (v7.1.0)** : mesure de la couverture des instructions de `server.py` en terminal et génération du rapport HTML (`reports/coverage/index.html`).
- **`flake8` (v7.4.1)** & **`flake8-html` (v0.4.3)** : contrôle de conformité PEP 8 et génération du rapport qualité HTML (`reports/flake8/index.html`).

### 1.3. Approche TDD (Test-Driven Development)
Chaque anomalie ou évolution a été traitée selon le cycle **Rouge → Vert → Refactor** :
1. **Phase Rouge (Red)** : écriture des tests couvrant les cas d'erreur (*sad paths*) et les cas nominaux (*happy paths*) attendus pour reproduire le bogue ou spécifier la fonctionnalité avant modification de `server.py`.
2. **Phase Verte (Green)** : implémentation de la correction minimale et ciblée dans `server.py` et les templates Jinja2 jusqu'à ce que l'ensemble de la suite de tests passe au vert.
3. **Non-régression et fusion** : vérification complète de la suite de tests avant chaque fusion `--no-ff` de la branche dédiée vers `main`.

---

## 2. Méthode et architecture de test

### 2.1. Organisation selon la pyramide des tests
Conformément à la règle 4 du Guide de développement (*« Tests unitaires >> tests d'intégration >> tests fonctionnels »* et *« Essayez d'écrire deux fois plus de tests unitaires que de tests d'intégration ou de tests fonctionnels »*), les tests sont séparés dans trois sous-dossiers de `tests/` :

| Niveau de test | Dossier | Nombre de tests | Rôle |
|---|---|:---:|---|
| **Tests unitaires** | `tests/unit/` | **40** | Testent isolément chaque route, chaque règle métier (connexion, déduction, solde, plafond de 12 places, capacité, dates passées, saisies invalides, entités inconnues, tableau des points) et les filtres Jinja (`date_fr`, `sort_by_points`). |
| **Tests d'intégration** | `tests/integration/` | **8** | Vérifient dans `test_booking_flow.py` l'enchaînement de plusieurs routes (`/showSummary` → `/book/...` → `/purchasePlaces` → `/points` → `/logout`) et la cohérence de l'état partagé en mémoire. |
| **Tests fonctionnels** | `tests/functional/` | **5** | Simulent dans `test_user_journeys.py` des parcours utilisateurs complets de bout en bout (secrétaire en parcours nominal, parcours avec erreurs successives puis reprise, compétition entre deux secrétaires, visiteur non connecté). |
| **Total** | `tests/` | **53** | Ratio respecté : **40 tests unitaires** $\gg$ **8 tests d'intégration** $>$ **5 tests fonctionnels** ($40 > 2 \times (8 + 5) = 26$). |

### 2.2. Isolation des tests via la fixture `mock_data` (`tests/conftest.py`)
L'application stocke son état dans trois variables globales en mémoire (`server.clubs`, `server.competitions`, `server.bookings`). Afin d'éviter tout couplage aux fichiers `clubs.json` et `competitions.json` et toute pollution d'un test vers le suivant, la fixture `mock_data` marquée `autouse=True` dans `tests/conftest.py` utilise `monkeypatch.setattr` avant chaque test pour injecter :
- Trois clubs de test : `Test Club` (10 points), `Small Club` (4 points), `Lucky Club` (13 points).
- Trois compétitions de test : `Future Competition` (`2030-06-15 10:00:00`, 25 places), `Past Competition` (`2020-03-27 10:00:00`, 13 places), `Small Competition` (`2030-09-01 10:00:00`, 3 places).
- Un dictionnaire `server.bookings` vide (`{}`).

---

## 3. Tableau de synthèse des branches et commits

*(Note : aucune capture d'écran n'est présente dans `reports/captures/` ; l'ensemble des preuves d'exécution repose sur l'historique Git et les suites de tests automatisées ci-dessous.)*

| Branche | Exigence des spécifications / README | Problème constaté | Correction apportée | Tests ajoutés | Résultat `pytest` vérifié (avant → après sur la suite) | Hash commit (fusion `main`) |
|---|---|---|---|---:|---|---|
| `bug/email-inconnu` | *« Les secrétaires des clubs de l'organisation pourront utiliser leur adresse électronique pour se connecter »* / *« résoudre les bogues et ajouter la gestion des erreurs »* | Crash `IndexError: list index out of range` dans `/showSummary` si l'e-mail est inconnu ou vide. | Recherche sécurisée via `next(..., None)`, validation du champ vide (`.strip()`), message `flash` et redirection vers `index`. | +3 (total : 3) | Avant fix : `2 failed, 1 passed` (crash `IndexError` sur e-mail inconnu/vide) → Après commit : `3 passed` | `20fedc8` (`62dc321`) |
| `bug/deduction-points` | *« Les points utilisés doivent être déduits du total précédent. »* (Phase 1) | Lors d'un achat dans `/purchasePlaces`, seules les places de la compétition diminuaient ; le solde `club['points']` restait inchangé. | Déduction de `placesRequired` sur `club['points']` et mention du nombre de places réservées dans le message de confirmation. | +2 (total : 5) | Avant fix : `2 failed` sur les nouveaux tests (`club['points']` restait à 13 au lieu de 11) → Après commit : `5 passed` | `04ab86d` (`970141f`) |
| `bug/points-insuffisants` | *« Il doit recevoir un message d'erreur si le club n'a pas assez de points »* (Le Comment, 2.b.ii) | Un club pouvait réserver plus de places que son solde de points, faisant passer son solde en négatif. | Contrôle `if placesRequired > int(club['points'])` avant déduction, affichage d'un message d'erreur et maintien de l'état. | +2 (total : 7) | Avant fix : `1 failed, 1 passed` (réservation de 6 places avec 4 points acceptée à tort) → Après commit : `7 passed` | `e588325` (`2f2551e`) |
| `bug/max-12-places` | *« chaque club ne peut inscrire qu'un maximum de 12 athlètes »* / *« pas pouvoir réserver [...] plus de 12 places dans une compétition »* | Aucun contrôle n'empêchait un club de réserver plus de 12 places en une seule fois ou en plusieurs réservations cumulées. | Ajout de `MAX_PLACES_PER_COMPETITION = 12` et du registre `bookings[(club, competition)]` vérifiant le cumul avant validation. | +3 (total : 10) | Avant fix : `2 failed, 1 passed` (13 places d'un coup et 10+3 places acceptées à tort) → Après commit : `10 passed` | `e8a8714` (`c14f74c`) |
| `bug/surreservation` | *« Il faut éviter la surréservation. »* / *« Ils ne doivent pas pouvoir réserver plus de places que celles disponibles »* | Un club pouvait réserver plus de places que la capacité restante de la compétition (`numberOfPlaces` devenait négatif). | Contrôle `if placesRequired > int(competition['numberOfPlaces'])` avec message d'erreur indiquant le nombre de places restantes. | +2 (total : 12) | Avant fix : `1 failed, 1 passed` (5 places réservées sur une compétition à 3 places) → Après commit : `12 passed` | `1e2acab` (`1038a87`) |
| `bug/competition-passee` | *« Le secrétaire identifie un événement à venir et clique sur celui-ci »* / *« inscrire des athlètes à de futures compétitions »* | Les compétitions dont la date était échue (ex. 2020) restaient réservables via `/book/...` et `/purchasePlaces`. | Création de `isPastCompetition(competition)` bloquant l'accès au formulaire dans `/book` et l'achat dans `/purchasePlaces`. | +4 (total : 16) | Avant fix : `2 failed, 2 passed` (compétition de 2020 acceptée à tort) → Après commit : `16 passed` | `c309a15` (`030f371`) |
| `bug/saisie-invalide` | *« Il y a plusieurs bogues, dont un qui fait planter l'application ! [...] résoudre les bogues et ajouter la gestion des erreurs. »* | Crash `ValueError` sur saisie vide ou texte dans `int(request.form['places'])`, et ajout frauduleux de points/places avec un nombre négatif ou nul. | Bloc `try / except ValueError` et refus de toute valeur `placesRequired <= 0` avec message d'erreur explicite. | +5 (total : 21) | Avant fix : `4 failed, 1 passed` (crash `ValueError` sur `""`/`"abc"`, acceptation de `0` et `-3`) → Après commit : `21 passed` | `e4e0e8a` (`b951f26`) |
| `bug/page-reservation-inconnue` | *« résoudre les bogues et ajouter la gestion des erreurs »* (routes `/book` et `/purchasePlaces`) | Crash `IndexError` si le nom du club ou de la compétition dans `/book/<competition>/<club>` ou `/purchasePlaces` n'existe pas (et bug `club` string passé à `welcome.html`). | Remplacement des compréhensions `[...][0]` par `next(..., None)` avec redirection vers `index` si club inconnu ou retour à `welcome.html` si compétition inconnue. | +5 (total : 26) | Avant fix : `4 failed, 1 passed` (crash `IndexError` sur club ou compétition inexistants) → Après commit : `26 passed` | `e25b166` (`7ed2ec0`) |
| `feature/tableau-points` | *« Par souci de transparence, il devrait y avoir un tableau public, en lecture seule, des totaux de points indiquant le nombre de points disponibles pour chaque club. Il ne devrait pas être nécessaire de se connecter au site pour voir la page. »* (Phase 2) | La route d'affichage des points (`# TODO: Add route for points display`) n'était pas implémentée. | Ajout de la route `GET /points`, du template `templates/points.html` et des liens de navigation sur `index.html` et `welcome.html`. | +5 (total : 31) | Avant implémentation : `404 Not Found` sur `GET /points` → Après commit : `31 passed` | `5cbbf17` (`5975976`) |
| `feature/traduction-francais` | Amélioration non exigée par les spécifications : interface en français et dates lisibles | Textes d'interface et messages d'erreur en anglais, dates affichées au format brut ISO `YYYY-MM-DD HH:MM:SS`. | Traduction complète des templates et messages `flash`, ajout du filtre Jinja `date_fr` indépendant de la locale OS. | +3 (total : 34) | Phase TDD rouge : `27 failed, 7 passed` → Après traduction et filtre `date_fr` : `34 passed` | `6488cce` (`caa8d1d`) |
| `feature/interface-graphique` | Amélioration non exigée par les spécifications : ergonomie et lisibilité de l'interface | Templates HTML bruts sans feuille de style, pas de distinction visuelle des messages de succès/erreur ni des compétitions terminées/complètes. | Création de `templates/base.html` et `static/css/style.css`, catégories `flash` (`success`/`error`), filtre `sort_by_points`, statuts `Ouverte`/`Complète`/`Terminée` et accords grammaticaux. | +6 (total : 40) | Suite enrichie de 34 à 40 tests unitaires : `40 passed` | `1eeb824` (`b882c5e`) |
| `amelioration/tests-integration-fonctionnels` | *« Tests unitaires >> tests d'intégration >> tests fonctionnels [...] regrouper les tests unitaires, d'intégration et fonctionnels dans des dossiers séparés. »* (Guide 4.d–g) | Seuls les tests unitaires étaient présents ; absence de compétition future dans `competitions.json`. | Ajout de `Winter Cup` (2027) dans `competitions.json`, création de 8 tests d'intégration (`test_booking_flow.py`) et 5 tests fonctionnels (`test_user_journeys.py`). | +13 (total : 53) | Avant ajout : `40 passed` → Après ajout : `53 passed` (`100 %` de couverture sur `server.py`) | `98f83b6` (`bbf2636`) |
| `amelioration/performance-qualite` | Guide 5 et Phase 2 sur la performance (*« pas plus de 5 s pour récupérer une liste de compétitions, et pas plus de 2 s pour mettre à jour le total de points »*, 6 utilisateurs) ; qualité PEP 8 et portabilité (Guide 1.d). | Absence de tests Locust ; `flake8` signalait 20 erreurs ; `requirements.txt` avec BOM UTF-8 et `pywin32` (ininstallable sur macOS/Linux) ; `README.md` en anglais. | Scénario Locust (`tests/performance/locustfile.py`, 6 utilisateurs) et rapports HTML/CSV ; `.flake8` et corrections PEP 8 (`20 → 0 erreur`) ; `requirements.txt` rendu multiplateforme (UTF-8 sans BOM) ; `README.md` en français. | +0 pytest (3 tâches Locust) | `53 passed` (`flake8` : `20 → 0 erreur`) | `a449bd7` (`7c3ba3a`) |
| `amelioration/rapports` | Rédaction des rapports de tests (`reports/RAPPORT_DE_TESTS.md`) et de performance (`reports/RAPPORT_DE_PERFORMANCE.md`). | Absence de documentation récapitulative des tests TDD par branche/bogue et de l'analyse détaillée des tirs Locust. | Création de `reports/RAPPORT_DE_TESTS.md` et `reports/RAPPORT_DE_PERFORMANCE.md`, comptage des réponses acceptées/refusées dans `locustfile.py` et référencement dans `README.md`. | +0 (total : 53) | `53 passed` (`flake8` : `0 erreur`) | `e993af3` (`ed50cf8`) |

---

## 4. Analyse détaillée par bogue (Phase 1)

### 4.1. Bogue 1 — Connexion avec une adresse e-mail inconnue ou vide (`bug/email-inconnu`)
- **Description** : Dans le code initial, `showSummary()` recherchait le club avec `[club for club in clubs if club['email'] == request.form['email']][0]`.
- **Étapes de reproduction** :
  1. Ouvrir la page d'accueil `/`.
  2. Soumettre une adresse e-mail absente de `clubs.json` (ex. `inconnu@club.com`) ou un champ vide.
- **Comportement attendu** : Redirection vers la page de connexion `/` avec un message d'erreur clair indiquant que l'adresse e-mail est introuvable ou requise.
- **Comportement observé avant correction** : Plante avec une erreur serveur `500 Internal Server Error` (`IndexError: list index out of range`). De plus, `index.html` n'affichait pas les messages `flash`.
- **Correction apportée** : Utilisation de `request.form.get('email', '').strip()` et `next((club for club in clubs if club['email'] == email), None)`, ajout des messages `flash` dans `server.py` et affichage de `get_flashed_messages()` dans `templates/index.html`.
- **Tests (`tests/unit/test_show_summary.py`)** :
  - *Happy path* : `test_valid_email_shows_welcome_page`
  - *Sad paths* : `test_unknown_email_returns_to_login_with_error`, `test_empty_email_returns_to_login_with_error`

### 4.2. Bogue 2 — Non-déduction des points du club après réservation (`bug/deduction-points`)
- **Description** : La route `/purchasePlaces` diminuait uniquement `competition['numberOfPlaces']` sans jamais mettre à jour `club['points']`.
- **Étapes de reproduction** :
  1. Se connecter avec un club ayant 13 points (`Lucky Club`).
  2. Réserver 2 places sur une compétition future.
- **Comportement attendu** : Le solde du club passe de 13 à 11 points et un message confirme le nombre de places réservées.
- **Comportement observé avant correction** : Le solde du club restait à 13 points indéfiniment.
- **Correction apportée** : Ajout de `club['points'] = clubPoints - placesRequired` dans `purchasePlaces()` et affichage du nombre exact de places réservées (accordé au singulier/pluriel) dans le message de confirmation.
- **Tests (`tests/unit/test_purchase_places.py`)** :
  - *Happy paths* : `test_booking_deducts_club_points_and_competition_places`, `test_booking_confirmation_singular_for_one_place`, `test_booking_confirmation_plural_for_multiple_places`

### 4.3. Bogue 3 — Réservation supérieure au solde de points du club (`bug/points-insuffisants`)
- **Description** : Aucun contrôle ne vérifiait que le club disposait d'assez de points pour couvrir le nombre de places demandées.
- **Étapes de reproduction** :
  1. Se connecter avec `Small Club` (4 points).
  2. Demander 6 places sur `Future Competition` (25 places disponibles).
- **Comportement attendu** : Refus de la réservation, message d'erreur explicite et conservation des 4 points du club et des 25 places de la compétition.
- **Comportement observé avant correction** : La réservation était validée et le solde du club passait à `-2` points.
- **Correction apportée** : Vérification `if placesRequired > clubPoints:` renvoyant un message `flash` d'erreur sans modifier ni le club ni la compétition.
- **Tests (`tests/unit/test_purchase_places.py`)** :
  - *Happy path* : `test_booking_exactly_all_points_is_accepted`
  - *Sad paths* : `test_booking_more_places_than_points_is_refused_plural`, `test_booking_more_places_than_points_is_refused_singular`

### 4.4. Bogue 4 — Dépassement de la limite de 12 places par club et par compétition (`bug/max-12-places`)
- **Description** : Un club disposant de plus de 12 points pouvait réserver plus de 12 places sur une même compétition, en une seule fois (ex. 13 places) ou en plusieurs fois (ex. 10 puis 3 places).
- **Étapes de reproduction** :
  1. Se connecter avec `Lucky Club` (13 points).
  2. Réserver 13 places d'un coup (ou 10 places puis 3 places) sur `Future Competition`.
- **Comportement attendu** : Refus de toute réservation portant le total du club sur cette compétition au-delà de 12 places.
- **Comportement observé avant correction** : Les 13 places étaient réservées sans erreur.
- **Correction apportée** : Création du dictionnaire `bookings = {}` indexé par `(club['name'], competition['name'])` et vérification `if alreadyBooked + placesRequired > MAX_PLACES_PER_COMPETITION:` (`12`).
- **Tests (`tests/unit/test_purchase_places.py`)** :
  - *Happy path* : `test_booking_exactly_12_places_is_accepted`
  - *Sad paths* : `test_booking_more_than_12_places_at_once_is_refused`, `test_cumulative_bookings_over_12_places_are_refused`

### 4.5. Bogue 5 — Surréservation au-delà de la capacité de la compétition (`bug/surreservation`)
- **Description** : Un club pouvait réserver plus de places que le nombre de places restantes dans une compétition.
- **Étapes de reproduction** :
  1. Choisir `Small Competition` (3 places disponibles) avec `Lucky Club` (13 points).
  2. Réserver 5 places.
- **Comportement attendu** : Refus de la réservation avec un message indiquant le nombre de places restantes (3 places).
- **Comportement observé avant correction** : La réservation aboutissait et le nombre de places de la compétition devenait `-2`.
- **Correction apportée** : Vérification `if placesRequired > availablePlaces:` avant toute déduction.
- **Tests (`tests/unit/test_purchase_places.py`)** :
  - *Happy path* : `test_booking_all_remaining_places_marks_competition_full`
  - *Sad paths* : `test_booking_more_places_than_available_is_refused_plural`, `test_booking_more_places_than_available_is_refused_singular`

### 4.6. Bogue 6 — Réservation sur une compétition passée (`bug/competition-passee`)
- **Description** : L'application permettait d'accéder à la page de réservation et d'acheter des places sur des compétitions dont la date était déjà passée (ex. `Spring Festival` et `Fall Classic` en 2020).
- **Étapes de reproduction** :
  1. Se connecter et cliquer sur la réservation d'une compétition de 2020 (`/book/Past Competition/Test Club`) ou soumettre `POST /purchasePlaces` sur cette compétition.
- **Comportement attendu** : Interdiction d'accéder au formulaire de réservation et de réserver sur une compétition passée, avec affichage du statut `"Terminée"` sur le calendrier.
- **Comportement observé avant correction** : Le formulaire s'affichait et la réservation était validée.
- **Correction apportée** : Fonction `isPastCompetition(competition)` comparant `datetime.strptime(competition['date'], "%Y-%m-%d %H:%M:%S")` à `datetime.now()`, appelée dans `book()`, `purchasePlaces()` et `welcome.html`.
- **Tests (`tests/unit/test_past_competition.py`)** :
  - *Happy paths* : `test_booking_future_competition_is_accepted`, `test_booking_page_of_future_competition_shows_form`
  - *Sad paths* : `test_booking_past_competition_is_refused`, `test_booking_page_of_past_competition_shows_error_without_form`, `test_welcome_page_shows_past_competition_as_finished_without_button`

### 4.7. Bogue 7 — Saisie invalide du nombre de places (`bug/saisie-invalide`)
- **Description** : `int(request.form['places'])` provoquait un crash `ValueError` si le champ était vide ou contenait du texte, et acceptait `0` ou un entier négatif (ce qui augmentait frauduleusement le solde de points du club et les places de la compétition).
- **Étapes de reproduction** :
  1. Soumettre `places=""`, `places="abc"`, `places="0"` ou `places="-3"` à `POST /purchasePlaces`.
- **Comportement attendu** : Aucun crash serveur ; refus de toute saisie non entière ou $\le 0$ avec message d'erreur et état inchangé.
- **Comportement observé avant correction** : Crash `ValueError` sur `""` et `"abc"`, et ajout de 3 points au club sur `"-3"`.
- **Correction apportée** : Conversion protégée par `try / except ValueError` et contrôle `if placesRequired <= 0:`.
- **Tests (`tests/unit/test_places_input.py`)** :
  - *Happy path* : `test_booking_one_place_is_accepted`
  - *Sad paths* : `test_booking_zero_places_is_refused`, `test_booking_negative_places_is_refused_and_points_do_not_increase`, `test_booking_text_places_does_not_crash`, `test_booking_empty_places_does_not_crash`

### 4.8. Bogue 8 — Club ou compétition inexistants dans `/book` et `/purchasePlaces` (`bug/page-reservation-inconnue`)
- **Description** : Les recherches `[c for c in clubs if ...][0]` et `[c for c in competitions if ...][0]` provoquaient un `IndexError` dès que l'URL `/book/<competition>/<club>` ou les données POST de `/purchasePlaces` référençaient un club ou une compétition inexistants.
- **Étapes de reproduction** :
  1. Accéder à `/book/Unknown Competition/Test Club` ou `/book/Future Competition/Unknown Club`.
  2. Soumettre `POST /purchasePlaces` avec un nom de club ou de compétition inconnu.
- **Comportement attendu** : Redirection vers la page de connexion si le club est inconnu, ou retour à la page d'accueil du club avec un message d'erreur si la compétition est inconnue.
- **Comportement observé avant correction** : Crash `500 Internal Server Error` (`IndexError`).
- **Correction apportée** : Recherche sécurisée par `next(..., None)` sur le club puis sur la compétition dans `book()` et `purchasePlaces()`.
- **Tests (`tests/unit/test_unknown_club_competition.py`)** :
  - *Happy path* : `test_booking_page_with_existing_future_competition_and_club_shows_form`
  - *Sad paths* : `test_booking_page_with_unknown_competition_shows_error`, `test_booking_page_with_unknown_club_redirects_to_login`, `test_purchase_with_unknown_competition_shows_error_and_changes_nothing`, `test_purchase_with_unknown_club_redirects_to_login_and_changes_nothing`

---

## 5. Résultats finaux, Couverture et Qualité du Code

### 5.1. Répartition finale des 53 tests
- **Tests unitaires (`tests/unit/`)** : **40 tests**
- **Tests d'intégration (`tests/integration/`)** : **8 tests**
- **Tests fonctionnels (`tests/functional/`)** : **5 tests**
- **Total** : **53 tests passants (`53 passed`)**

### 5.2. Sortie de `pytest` et Couverture (`100 %`)
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\HP\Documents\Python_Testing_2627
plugins: locust-2.47.0, cov-7.1.0, flask-1.3.0
collected 53 items

tests\functional\test_user_journeys.py .....                             [  9%]
tests\integration\test_booking_flow.py ........                          [ 24%]
tests\unit\test_past_competition.py .....                                [ 33%]
tests\unit\test_places_input.py .....                                    [ 43%]
tests\unit\test_points_board.py ......                                   [ 54%]
tests\unit\test_purchase_places.py ...........                           [ 75%]
tests\unit\test_show_summary.py .......                                  [ 88%]
tests\unit\test_unknown_club_competition.py .....                        [100%]

=============================== tests coverage ================================
Name        Stmts   Miss  Cover   Missing
-----------------------------------------
server.py     114      0   100%
-----------------------------------------
TOTAL         114      0   100%
============================= 53 passed in 0.51s ==============================
```

### 5.3. Rapports HTML générés
- **Rapport de couverture HTML (`100 %`)** : [reports/coverage/index.html](coverage/index.html)
- **Rapport de qualité Flake8 HTML (`0 erreur`)** : [reports/flake8/index.html](flake8/index.html)

---

## 6. Limites connues

1. **Absence de session de connexion (`flask.session`)** : conformément à l'architecture du POC initial et afin de ne pas modifier les signatures de routes ni les formulaires, l'application n'utilise pas de cookie de session pour maintenir l'authentification ; le nom du club est transmis dans l'URL (`/book/<competition>/<club>`) et via le champ caché `<input type="hidden" name="club">` du formulaire de réservation.
2. **Données en mémoire réinitialisées au redémarrage** : les fichiers `clubs.json` et `competitions.json` sont lus uniquement au démarrage de l'application (`loadClubs()` et `loadCompetitions()`). Les réservations et déductions de points sont conservées en mémoire vive pendant l'exécution du serveur mais sont réinitialisées à chaque redémarrage.
