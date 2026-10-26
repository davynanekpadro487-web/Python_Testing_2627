"""Tests unitaires : interdiction de réserver une compétition passée
(routes /book/<competition>/<club> et /purchasePlaces)."""
import html

import server


PAST_COMPETITION_ERROR = "Cette compétition a déjà eu lieu, la réservation n'est pas possible."


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def book(client, club, competition, places):
    return client.post(
        "/purchasePlaces",
        data={"club": club, "competition": competition, "places": places},
    )


def get(collection, name):
    return next(item for item in collection if item["name"] == name)


# --- Sad path : /purchasePlaces sur une compétition passée (2020) ---

def test_booking_past_competition_is_refused(client):
    response = book(client, "Test Club", "Past Competition", "2")
    body = text_of(response)

    assert response.status_code == 200
    assert PAST_COMPETITION_ERROR in body
    assert "flash-error" in body
    assert "Réservation confirmée" not in body
    # Rien n'est modifié : ni les points du club, ni les places, ni le registre.
    assert int(get(server.clubs, "Test Club")["points"]) == 10
    assert int(get(server.competitions, "Past Competition")["numberOfPlaces"]) == 13
    assert server.bookings == {}


# --- Sad path : page /book/<competition>/<club> d'une compétition passée ---

def test_booking_page_of_past_competition_shows_error_without_form(client):
    response = client.get("/book/Past Competition/Test Club")
    body = text_of(response)

    assert response.status_code == 200
    assert PAST_COMPETITION_ERROR in body
    assert "<form" not in body
    assert "/purchasePlaces" not in body


def test_welcome_page_shows_past_competition_as_finished_without_button(client):
    response = client.post("/showSummary", data={"email": "test@club.com"})
    body = text_of(response)

    assert response.status_code == 200
    assert "Terminée" in body
    assert "/book/Past%20Competition/Test%20Club" not in body
    assert "/book/Future%20Competition/Test%20Club" in body


# --- Happy path : compétition future (2030) ---

def test_booking_future_competition_is_accepted(client):
    response = book(client, "Test Club", "Future Competition", "2")
    body = text_of(response)

    assert response.status_code == 200
    assert "Réservation confirmée : 2 places réservées." in body
    assert PAST_COMPETITION_ERROR not in body
    assert int(get(server.clubs, "Test Club")["points"]) == 8
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 23


def test_booking_page_of_future_competition_shows_form(client):
    response = client.get("/book/Future Competition/Test Club")
    body = text_of(response)

    assert response.status_code == 200
    assert "<form" in body
    assert PAST_COMPETITION_ERROR not in body
