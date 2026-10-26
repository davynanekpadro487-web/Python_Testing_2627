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
    2. `Mise à jour des points` (`POST /purchasePlaces`, `club=Simply Lift`, `competition=Winter Cup`, `places=1`, avec `catch_response=True` comptabilisant dans `booking_stats` les réponses contenant `"Réservation confirmée"` vs les refus métier, sans marquer ces derniers comme des échecs HTTP)
    3. `Tableau des points` (`GET /points`)
  - Écouteur `@events.quitting.add_listener` (`log_booking_stats`) : affiche à la fin du tir le décompte exact des réservations confirmées et des refus métier.
- **Environnement d'exécution** :
  - Système d'exploitation : **Windows 10/11 (64 bits, PowerShell)**
  - Interpréteur : **Python 3.11.9** dans l'environnement virtuel `venv`
  - Serveur cible : **Flask 3.1.3** fraîchement redémarré sur les données initiales (`http://127.0.0.1:5000`)
- **Paramètres du tir de charge** :
  - Nombre d'utilisateurs simultanés (`-u`) : **6 utilisateurs**
  - Vitesse d'apparition (`-r`) : **6 utilisateurs / seconde**
  - Durée totale (`-t`) : **60 secondes**
- **Commande exacte exécutée** :
  ```powershell
  .\venv\Scripts\Activate.ps1
  locust -f tests/performance/locustfile.py --headless -u 6 -r 6 -t 60s --host http://127.0.0.1:5000 --html reports/locust_report.html --csv reports/locust --only-summary
  ```

---

## 3. Tableau des résultats (`reports/locust_stats.csv`)

Les mesures ci-dessous sont extraites directement du fichier [`reports/locust_stats.csv`](locust_stats.csv) généré à l'issue du test de 60 secondes sur un serveur fraîchement démarré :

| Type | Requête (`Name`) | Requêtes | Échecs | Moyenne (ms) | Médiane / p50 (ms) | p95 (ms) | Max (ms) | Débit (req/s) | Seuil max | Conformité |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| `POST` | **Chargement des compétitions** (`/showSummary`) | 84 | 0 (0 %) | **17,76 ms** | **6 ms** | **110 ms** | **130,16 ms** | 1,44 | 5000 ms (5 s) | ✅ Conforme |
| `POST` | **Mise à jour des points** (`/purchasePlaces`) | 44 | 0 (0 %) | **8,55 ms** | **5 ms** | **18 ms** | **49,89 ms** | 0,76 | 2000 ms (2 s) | ✅ Conforme |
| `GET` | **Tableau des points** (`/points`) | 55 | 0 (0 %) | **7,95 ms** | **4 ms** | **32 ms** | **37,93 ms** | 0,94 | 2000 ms (2 s) | ✅ Conforme |
| — | **Total / Agrégé (`Aggregated`)** | **183** | **0 (0 %)** | **12,60 ms** | **5 ms** | **38 ms** | **130,16 ms** | **3,14** | — | ✅ **100 % OK** |

---

## 4. Analyse des performances

1. **Chargement de la liste des compétitions (`POST /showSummary`)** :
   - Temps moyen : **17,76 ms** (médiane à **6 ms**, 95e percentile à **110 ms**, maximum observé à **130,16 ms**).
   - Le temps maximal mesuré est **38 fois inférieur** au seuil de **5 secondes (`5000 ms`)** exigé par les spécifications.
2. **Mise à jour du total de points (`POST /purchasePlaces`)** :
   - Temps moyen : **8,55 ms** (médiane à **5 ms**, 95e percentile à **18 ms**, maximum observé à **49,89 ms**).
   - Le temps maximal mesuré est **40 fois inférieur** au seuil de **2 secondes (`2000 ms`)** exigé par les spécifications (et plus de 110 fois inférieur au 95e percentile).
3. **Consultation du tableau public des points (`GET /points`)** :
   - Malgré le tri dynamique des clubs par ordre décroissant de points (`sort_by_points`), le temps moyen est de **7,95 ms** (p95 à **32 ms**, maximum à **37,93 ms**).
4. **Fiabilité sous charge** :
   - Sur les **183 requêtes** envoyées par les 6 utilisateurs simultanés pendant 60 secondes, **aucun échec HTTP (`0 %`)** ni aucune exception n'ont été enregistrés.

---

## 5. Point de vigilance méthodologique (en toute transparence)

Le compteur intégré dans [`tests/performance/locustfile.py`](../tests/performance/locustfile.py) (`catch_response=True` détectant la présence de `"Réservation confirmée"` dans le HTML retourné) affiche en fin de tir le bilan exact suivant :

```text
[Bilan Mise à jour des points] Total=44 | Réservations confirmées=12 | Refus métier=32
```

Sur un serveur fraîchement démarré (données initiales : `Simply Lift` dispose de 13 points et `Winter Cup` de 20 places), la tâche `Mise à jour des points` a exécuté **44 requêtes** `POST /purchasePlaces` demandant chacune `1` place :
- **12 requêtes ont abouti (`Réservations confirmées=12`)** : elles empruntent le chemin nominal (*happy path*) avec déduction effective d'1 point sur le club et d'1 place sur la compétition, mise à jour du dictionnaire `bookings` jusqu'au plafond réglementaire de **12 places maximum par club et par compétition**, et rendu de `welcome.html` avec le message de confirmation.
- **32 requêtes ont été refusées (`Refus métier=32`)** : une fois le plafond de 12 places atteint par `Simply Lift` sur `Winter Cup`, les requêtes suivantes exécutent la recherche du club, la recherche de la compétition, la validation du nombre de places, la vérification de la date et de la capacité, puis le contrôle du plafond dans `bookings`, avant de rendre le template complet `welcome.html` avec le message `flash` d'erreur (statut HTTP `200`).
- **Impact sur la mesure** : dans les deux cas (les 12 réservations confirmées comme les 32 refus métier), la route `POST /purchasePlaces` exécute l'intégralité des contrôles métier et le rendu Jinja2 complet de `welcome.html`. Le temps de réponse reste systématiquement très inférieur au seuil de **2 secondes** (médiane **5 ms**, moyenne **8,55 ms**, p95 **18 ms**, maximum absolu **49,89 ms**).

---

## 6. Rapports complets générés

- **Rapport interactif HTML Locust** : [reports/locust_report.html](locust_report.html)
- **Statistiques détaillées CSV** : [reports/locust_stats.csv](locust_stats.csv) · [reports/locust_stats_history.csv](locust_stats_history.csv)
