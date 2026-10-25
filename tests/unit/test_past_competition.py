"""Tests unitaires : interdiction de réserver une compétition passée
(routes /book/<competition>/<club> et /purchasePlaces)."""
import server


PAST_COMPETITION_ERROR = b"This competition has already taken place, booking is not possible."


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

    assert response.status_code == 200
    assert PAST_COMPETITION_ERROR in response.data
    assert b"Great-booking complete!" not in response.data
    # Rien n'est modifié : ni les points du club, ni les places, ni le registre.
    assert int(get(server.clubs, "Test Club")["points"]) == 10
    assert int(get(server.competitions, "Past Competition")["numberOfPlaces"]) == 13
    assert server.bookings == {}


# --- Sad path : page /book/<competition>/<club> d'une compétition passée ---

def test_booking_page_of_past_competition_shows_error_without_form(client):
    response = client.get("/book/Past Competition/Test Club")

    assert response.status_code == 200
    assert PAST_COMPETITION_ERROR in response.data
    assert b"<form" not in response.data
    assert b"/purchasePlaces" not in response.data


# --- Happy path : compétition future (2030) ---

def test_booking_future_competition_is_accepted(client):
    response = book(client, "Test Club", "Future Competition", "2")

    assert response.status_code == 200
    assert b"Great-booking complete! You booked 2 places." in response.data
    assert PAST_COMPETITION_ERROR not in response.data
    assert int(get(server.clubs, "Test Club")["points"]) == 8
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 23


def test_booking_page_of_future_competition_shows_form(client):
    response = client.get("/book/Future Competition/Test Club")

    assert response.status_code == 200
    assert b"<form" in response.data
    assert PAST_COMPETITION_ERROR not in response.data
