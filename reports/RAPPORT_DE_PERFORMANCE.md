# Rapport de Performance — Projet GUDLFT (`Python_Testing_2627`)

## 1. Objectif et exigences

Conformément aux [Spécifications fonctionnelles](../Spécifications+fonctionnelles.pdf) (Phase 2 et section 5 « La Performance » du Guide de développement) :
> - *« Compte tenu du nombre d'utilisateurs potentiels, il faut réduire au minimum les temps de construction et de rendu ; il ne devrait pas falloir plus de 5 secondes pour récupérer une liste de compétitions, et pas plus de 2 secondes pour mettre à jour le total de points. »*
> - *« Utilisez Locust pour vous assurer que le temps de chargement ne dépasse jamais 5 secondes, et que les mises à jour ne prennent pas plus de 2 secondes. »*
> - *« Le nombre d'utilisateurs par défaut pour les tests de performance est de six utilisateurs. »*

| Opération évaluée | Route Flask | Seuil maximal exigé | Charge exigée |
|---|---|:---:|:---:|
| **Chargement de la liste des compétitions** | `POST /showSummary` | **< 5 s** (`5000 ms`) | 6 utilisateurs simultanés |
| **Mise à jour du total de points** | `POST /purchasePlaces` | **< 2 s** (`2000 ms`) | 6 utilisateurs simultanés |
| **Consultation du tableau public des points** | `GET /points` | **< 2 s** (`2000 ms`) | 6 utilisateurs simultanés |

---

## 2. Protocole de test

- **Outil** : **Locust v2.47.0**
- **Fichier de scénario** : [`tests/performance/locustfile.py`](../tests/performance/locustfile.py)
  - Classe `GudlftUser(HttpUser)` avec un temps d'attente `wait_time = between(1, 3)` secondes entre deux tâches.
  - Méthode `on_start` : connexion initiale sur `POST /showSummary` avec le compte `john@simplylift.co` (*Simply Lift*).
  - Trois tâches de poids égal (`@task(2)`) nommées explicitement :
    1. `Chargement des compétitions` (`POST /showSummary`, `email=john@simplylift.co`)
    2. `Mise à jour des points` (`POST /purchasePlaces`, `club=Simply Lift`, `competition=Winter Cup`, `places=1`)
    3. `Tableau des points` (`GET /points`)
- **Environnement d'exécution** :
  - Système d'exploitation : **Windows 10/11 (64 bits, PowerShell)**
  - Interpréteur : **Python 3.11.9** dans l'environnement virtuel `venv`
  - Serveur cible : **Flask 3.1.3** (`http://127.0.0.1:5000`)
- **Paramètres du tir de charge** :
  - Nombre d'utilisateurs simultanés (`-u`) : **6 utilisateurs**
  - Vitesse d'apparition (`-r`) : **6 utilisateurs / seconde**
  - Durée totale (`-t`) : **60 secondes**
- **Commande exacte exécutée** :
  ```powershell
  .\venv\Scripts\Activate.ps1
  locust -f tests/performance/locustfile.py --headless -u 6 -r 6 -t 60s --host http://127.0.0.1:5000 --html reports/locust_report.html --csv reports/locust
  ```

---

## 3. Tableau des résultats (`reports/locust_stats.csv`)

Les mesures ci-dessous sont extraites directement du fichier [`reports/locust_stats.csv`](locust_stats.csv) généré à l'issue du test de 60 secondes :

| Type | Requête (`Name`) | Requêtes | Échecs | Moyenne (ms) | Médiane / p50 (ms) | p95 (ms) | Max (ms) | Débit (req/s) | Seuil max | Conformité |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| `POST` | **Chargement des compétitions** (`/showSummary`) | 74 | 0 (0 %) | **18,71 ms** | **11 ms** | **110 ms** | **119,54 ms** | 1,27 | 5000 ms (5 s) | ✅ Conforme |
| `POST` | **Mise à jour des points** (`/purchasePlaces`) | 56 | 0 (0 %) | **13,96 ms** | **8 ms** | **18 ms** | **266,08 ms** | 0,96 | 2000 ms (2 s) | ✅ Conforme |
| `GET` | **Tableau des points** (`/points`) | 53 | 0 (0 %) | **10,86 ms** | **7 ms** | **30 ms** | **80,67 ms** | 0,91 | 2000 ms (2 s) | ✅ Conforme |
| — | **Total / Agrégé (`Aggregated`)** | **183** | **0 (0 %)** | **14,98 ms** | **8 ms** | **30 ms** | **266,08 ms** | **3,14** | — | ✅ **100 % OK** |

---

## 4. Analyse des performances

1. **Chargement de la liste des compétitions (`POST /showSummary`)** :
   - Temps moyen : **18,71 ms** (médiane à **11 ms**, 95e percentile à **110 ms**, maximum observé à **119,54 ms**).
   - Le temps maximal mesuré est **41 fois inférieur** au seuil de **5 secondes (`5000 ms`)** exigé par les spécifications.
2. **Mise à jour du total de points (`POST /purchasePlaces`)** :
   - Temps moyen : **13,96 ms** (médiane à **8 ms**, 95e percentile à **18 ms**, maximum observé à **266,08 ms**).
   - Le temps maximal mesuré est **7,5 fois inférieur** au seuil de **2 secondes (`2000 ms`)** exigé par les spécifications (et plus de 100 fois inférieur au 95e percentile).
3. **Consultation du tableau public des points (`GET /points`)** :
   - Malgré le tri dynamique des clubs par ordre décroissant de points (`sort_by_points`), le temps moyen est de **10,86 ms** (p95 à **30 ms**, maximum à **80,67 ms**).
4. **Fiabilité sous charge** :
   - Sur les **183 requêtes** envoyées par les 6 utilisateurs simultanés pendant 60 secondes, **aucun échec HTTP (`0 %`)** ni aucune exception n'ont été enregistrés.

---

## 5. Point de vigilance méthodologique (en toute transparence)

Au cours de la campagne de 60 secondes, la tâche `Mise à jour des points` a exécuté **56 requêtes** `POST /purchasePlaces` demandant chacune `1` place sur la compétition `Winter Cup` (20 places disponibles) pour le club `Simply Lift` (13 points initiaux) :
- Les **12 premières requêtes** suivent le chemin nominal (*happy path*) : déduction effective d'1 point sur le club et d'1 place sur la compétition, mise à jour du dictionnaire `bookings` jusqu'au plafond réglementaire de **12 places maximum par club et par compétition**, et affichage du bandeau de confirmation.
- Les **44 requêtes suivantes** atteignent la règle métier limitant un club à 12 places par compétition : elles exécutent la recherche du club, la recherche de la compétition, la validation du nombre de places, la vérification de la date et de la capacité, puis le contrôle du plafond dans `bookings`, avant de rendre le template complet `welcome.html` avec le message `flash` d'erreur (statut HTTP `200`).
- **Impact sur la mesure** : dans les deux cas (les 12 achats acceptés comme les 44 achats refusés), la route `POST /purchasePlaces` exécute l'intégralité des contrôles métier et le rendu Jinja2 complet de `welcome.html`. Le temps de réponse reste systématiquement très inférieur au seuil de **2 secondes** (médiane **8 ms**, p95 **18 ms**, maximum absolu **266,08 ms**).

---

## 6. Rapports complets générés

- **Rapport interactif HTML Locust** : [reports/locust_report.html](locust_report.html)
- **Statistiques détaillées CSV** : [reports/locust_stats.csv](locust_stats.csv) · [reports/locust_stats_history.csv](locust_stats_history.csv)
