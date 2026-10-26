"""Tests unitaires : club ou compétition inexistants dans /book et /purchasePlaces."""
import html

import server


CLUB_NOT_FOUND_ERROR = "Club introuvable, veuillez vous reconnecter."
COMPETITION_NOT_FOUND_ERROR = (
    "Compétition introuvable, veuillez choisir une compétition dans la liste."
)
LOGIN_PAGE = "Bienvenue sur le portail de réservation GUDLFT"


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def book(client, club, competition, places):
    return client.post(
        "/purchasePlaces",
        data={"club": club, "competition": competition, "places": places},
        follow_redirects=True,
    )


def snapshot():
    """Photographie des données pour vérifier que rien n'a été modifié."""
    return (
        [dict(c) for c in server.clubs],
        [dict(c) for c in server.competitions],
        dict(server.bookings),
    )


# --- Sad paths : /book/<competition>/<club> ---

def test_booking_page_with_unknown_competition_shows_error(client):
    response = client.get("/book/Unknown Competition/Test Club")
    body = text_of(response)

    assert response.status_code == 200
    assert COMPETITION_NOT_FOUND_ERROR in body
    assert "Bienvenue, test@club.com" in body
    assert "/purchasePlaces" not in body


def test_booking_page_with_unknown_club_redirects_to_login(client):
    response = client.get("/book/Future Competition/Unknown Club", follow_redirects=True)
    body = text_of(response)

    assert response.status_code == 200
    assert CLUB_NOT_FOUND_ERROR in body
    assert LOGIN_PAGE in body
    assert "/purchasePlaces" not in body


# --- Sad paths : POST /purchasePlaces ---

def test_purchase_with_unknown_competition_shows_error_and_changes_nothing(client):
    before = snapshot()

    response = book(client, "Test Club", "Unknown Competition", "2")
    body = text_of(response)

    assert response.status_code == 200
    assert COMPETITION_NOT_FOUND_ERROR in body
    assert "Bienvenue, test@club.com" in body
    assert "Réservation confirmée" not in body
    assert snapshot() == before


def test_purchase_with_unknown_club_redirects_to_login_and_changes_nothing(client):
    before = snapshot()

    response = book(client, "Unknown Club", "Future Competition", "2")
    body = text_of(response)

    assert response.status_code == 200
    assert CLUB_NOT_FOUND_ERROR in body
    assert LOGIN_PAGE in body
    assert "Réservation confirmée" not in body
    assert snapshot() == before


# --- Happy path ---

def test_booking_page_with_existing_future_competition_and_club_shows_form(client):
    response = client.get("/book/Future Competition/Test Club")
    body = text_of(response)

    assert response.status_code == 200
    assert "<form" in body
    assert "/purchasePlaces" in body
    assert 'value="Test Club"' in body
    assert 'value="Future Competition"' in body
