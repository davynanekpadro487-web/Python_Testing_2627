"""Tests unitaires : club ou compétition inexistants dans /book et /purchasePlaces."""
import server


CLUB_NOT_FOUND_ERROR = b"Club not found, please log in again."
COMPETITION_NOT_FOUND_ERROR = b"Competition not found, please choose a competition from the list."
LOGIN_PAGE = b"Welcome to the GUDLFT Registration Portal"


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

    assert response.status_code == 200
    assert COMPETITION_NOT_FOUND_ERROR in response.data
    assert b"Welcome, test@club.com" in response.data
    assert b"/purchasePlaces" not in response.data


def test_booking_page_with_unknown_club_redirects_to_login(client):
    response = client.get("/book/Future Competition/Unknown Club", follow_redirects=True)

    assert response.status_code == 200
    assert CLUB_NOT_FOUND_ERROR in response.data
    assert LOGIN_PAGE in response.data
    assert b"/purchasePlaces" not in response.data


# --- Sad paths : POST /purchasePlaces ---

def test_purchase_with_unknown_competition_shows_error_and_changes_nothing(client):
    before = snapshot()

    response = book(client, "Test Club", "Unknown Competition", "2")

    assert response.status_code == 200
    assert COMPETITION_NOT_FOUND_ERROR in response.data
    assert b"Welcome, test@club.com" in response.data
    assert b"Great-booking complete!" not in response.data
    assert snapshot() == before


def test_purchase_with_unknown_club_redirects_to_login_and_changes_nothing(client):
    before = snapshot()

    response = book(client, "Unknown Club", "Future Competition", "2")

    assert response.status_code == 200
    assert CLUB_NOT_FOUND_ERROR in response.data
    assert LOGIN_PAGE in response.data
    assert b"Great-booking complete!" not in response.data
    assert snapshot() == before


# --- Happy path ---

def test_booking_page_with_existing_future_competition_and_club_shows_form(client):
    response = client.get("/book/Future Competition/Test Club")

    assert response.status_code == 200
    assert b"<form" in response.data
    assert b"/purchasePlaces" in response.data
    assert b'value="Test Club"' in response.data
    assert b'value="Future Competition"' in response.data
