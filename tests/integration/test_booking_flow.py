"""Tests d'intégration enchaînant plusieurs routes et vérifiant l'état partagé."""
import html
import re

import server


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def row_pattern(name, points):
    """Vérifie la présence d'une ligne avec le club et ses points sur /points."""
    return re.compile(
        rf"<td>\s*{re.escape(name)}\s*</td>\s*<td>\s*{points}\s*</td>".encode()
    )


def test_login_book_and_points_updated_on_board(client):
    """Connexion -> réservation -> les points sont mis à jour sur /points."""
    login_response = client.post("/showSummary", data={"email": "test@club.com"})
    assert login_response.status_code == 200
    assert '<span class="points-figure">10</span>' in text_of(login_response)

    book_page = client.get("/book/Future Competition/Test Club")
    assert book_page.status_code == 200
    assert "Places restantes : 25" in text_of(book_page)

    purchase_response = client.post(
        "/purchasePlaces",
        data={
            "club": "Test Club",
            "competition": "Future Competition",
            "places": "4",
        },
    )
    purchase_body = text_of(purchase_response)
    assert purchase_response.status_code == 200
    assert "Réservation confirmée : 4 places réservées." in purchase_body
    assert '<span class="points-figure">6</span>' in purchase_body

    points_response = client.get("/points")
    assert points_response.status_code == 200
    assert row_pattern("Test Club", 6).search(points_response.data)


def test_successive_bookings_up_to_12_limit_then_refused(client):
    """Réservations successives du même club jusqu'à la limite de 12, puis refus."""
    client.post("/showSummary", data={"email": "lucky@club.com"})

    first_booking = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Future Competition",
            "places": "7",
        },
    )
    assert "Réservation confirmée : 7 places réservées." in text_of(first_booking)

    second_booking = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Future Competition",
            "places": "5",
        },
    )
    assert "Réservation confirmée : 5 places réservées." in text_of(second_booking)
    assert server.bookings[("Lucky Club", "Future Competition")] == 12

    third_booking = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Future Competition",
            "places": "1",
        },
    )
    assert (
        "Vous ne pouvez pas réserver plus de 12 places par compétition"
        in text_of(third_booking)
    )

    points_response = client.get("/points")
    assert row_pattern("Lucky Club", 1).search(points_response.data)


def test_two_clubs_booking_same_competition_updates_remaining_places(client):
    """Deux clubs réservent sur la même compétition, places restantes cohérentes."""
    client.post("/showSummary", data={"email": "lucky@club.com"})
    first_purchase = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Future Competition",
            "places": "8",
        },
    )
    first_body = text_of(first_purchase)
    assert "Réservation confirmée : 8 places réservées." in first_body
    assert "Places restantes : 17" in first_body

    client.post("/showSummary", data={"email": "test@club.com"})
    second_purchase = client.post(
        "/purchasePlaces",
        data={
            "club": "Test Club",
            "competition": "Future Competition",
            "places": "5",
        },
    )
    second_body = text_of(second_purchase)
    assert "Réservation confirmée : 5 places réservées." in second_body
    assert "Places restantes : 12" in second_body

    points_response = client.get("/points")
    assert row_pattern("Lucky Club", 5).search(points_response.data)
    assert row_pattern("Test Club", 5).search(points_response.data)


def test_refused_booking_insufficient_points_keeps_points_and_places(client):
    """Une réservation refusée (points insuffisants) ne modifie ni /points ni les places."""
    client.post("/showSummary", data={"email": "small@club.com"})

    refused_response = client.post(
        "/purchasePlaces",
        data={
            "club": "Small Club",
            "competition": "Future Competition",
            "places": "6",
        },
    )
    refused_body = text_of(refused_response)
    assert refused_response.status_code == 200
    assert "Vous n'avez pas assez de points" in refused_body
    assert "Places restantes : 25" in refused_body

    points_response = client.get("/points")
    assert row_pattern("Small Club", 4).search(points_response.data)


def test_access_past_competition_from_welcome_page_is_refused(client):
    """Accès à /book/... d'une compétition passée depuis la page welcome."""
    welcome_response = client.post("/showSummary", data={"email": "test@club.com"})
    welcome_body = text_of(welcome_response)
    assert welcome_response.status_code == 200
    assert "Past Competition" in welcome_body
    assert "Terminée" in welcome_body

    book_response = client.get("/book/Past Competition/Test Club")
    book_body = text_of(book_response)
    assert book_response.status_code == 200
    assert (
        "Cette compétition a déjà eu lieu, la réservation n'est pas possible."
        in book_body
    )
    assert "<form" not in book_body

    points_response = client.get("/points")
    assert row_pattern("Test Club", 10).search(points_response.data)


def test_refused_overbooking_competition_capacity_preserves_state(client):
    """Un refus pour capacité insuffisante laisse les places et /points intacts."""
    client.post("/showSummary", data={"email": "lucky@club.com"})
    book_page = client.get("/book/Small Competition/Lucky Club")
    assert "Places restantes : 3" in text_of(book_page)

    refused_response = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Small Competition",
            "places": "4",
        },
    )
    refused_body = text_of(refused_response)
    assert "Pas assez de places disponibles" in refused_body
    assert "Places restantes : 3" in refused_body

    points_response = client.get("/points")
    assert row_pattern("Lucky Club", 13).search(points_response.data)


def test_invalid_places_submission_does_not_modify_points_board(client):
    """Une saisie invalide (nombre négatif) ne modifie pas le tableau des points."""
    client.post("/showSummary", data={"email": "test@club.com"})
    client.get("/book/Future Competition/Test Club")

    neg_response = client.post(
        "/purchasePlaces",
        data={
            "club": "Test Club",
            "competition": "Future Competition",
            "places": "-3",
        },
    )
    assert "Veuillez saisir un nombre de places valide" in text_of(neg_response)

    points_response = client.get("/points")
    assert row_pattern("Test Club", 10).search(points_response.data)


def test_login_booking_and_logout_flow_redirects_to_index(client):
    """Enchaînement connexion -> réservation -> déconnexion -> consultation /points."""
    client.post("/showSummary", data={"email": "small@club.com"})
    client.post(
        "/purchasePlaces",
        data={
            "club": "Small Club",
            "competition": "Small Competition",
            "places": "2",
        },
    )

    logout_response = client.get("/logout", follow_redirects=True)
    assert logout_response.status_code == 200
    assert "Bienvenue sur le portail de réservation GUDLFT" in text_of(logout_response)

    points_response = client.get("/points")
    assert row_pattern("Small Club", 2).search(points_response.data)
