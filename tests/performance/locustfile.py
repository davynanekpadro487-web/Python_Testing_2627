"""Tests de performance Locust pour l'application GUDLFT.

Spécifications :
- Charge par défaut : 6 utilisateurs simultanés
- Chargement des compétitions (/showSummary) : < 5 s
- Mise à jour des points (/purchasePlaces) : < 2 s
"""
from locust import HttpUser, between, events, task

booking_stats = {"accepted": 0, "refused": 0}


@events.quitting.add_listener
def log_booking_stats(environment, **_kwargs):
    """Affiche en fin de tir le décompte exact des réservations acceptées et refusées."""
    total = booking_stats["accepted"] + booking_stats["refused"]
    print(
        f"\n[Bilan Mise à jour des points] Total={total} | "
        f"Réservations confirmées={booking_stats['accepted']} | "
        f"Refus métier={booking_stats['refused']}"
    )


class GudlftUser(HttpUser):
    """Simule un secrétaire de club interagissant avec l'application GUDLFT."""

    wait_time = between(1, 3)

    def on_start(self):
        """Connexion initiale du secrétaire du club Simply Lift."""
        self.client.post(
            "/showSummary",
            data={"email": "john@simplylift.co"},
            name="Chargement des compétitions",
        )

    @task(2)
    def load_competitions(self):
        """Chargement de la liste des compétitions (< 5 s)."""
        self.client.post(
            "/showSummary",
            data={"email": "john@simplylift.co"},
            name="Chargement des compétitions",
        )

    @task(2)
    def update_points(self):
        """Réservation d'1 place sur Winter Cup et mise à jour des points (< 2 s)."""
        with self.client.post(
            "/purchasePlaces",
            data={
                "club": "Simply Lift",
                "competition": "Winter Cup",
                "places": "1",
            },
            name="Mise à jour des points",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Statut HTTP inattendu : {response.status_code}")
            elif "Réservation confirmée" in response.text:
                booking_stats["accepted"] += 1
                response.success()
            else:
                booking_stats["refused"] += 1
                response.success()

    @task(2)
    def view_points_board(self):
        """Consultation du tableau public des points."""
        self.client.get(
            "/points",
            name="Tableau des points",
        )
