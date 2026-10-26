"""Tests unitaires : validation du nombre de places saisi dans /purchasePlaces."""
import html

import server


INVALID_PLACES_ERROR = "Veuillez saisir un nombre de places valide (un entier supérieur à 0)."


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def book(client, club, competition, places):
    return client.post(
        "/purchasePlaces",
        data={"club": club, "competition": competition, "places": places},
    )


def get(collection, name):
    return next(item for item in collection if item["name"] == name)


def assert_nothing_changed():
    assert int(get(server.clubs, "Test Club")["points"]) == 10
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 25
    assert server.bookings == {}


# --- Sad paths ---

def test_booking_zero_places_is_refused(client):
    response = book(client, "Test Club", "Future Competition", "0")
    body = text_of(response)

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in body
    assert "Réservation confirmée" not in body
    assert_nothing_changed()


def test_booking_negative_places_is_refused_and_points_do_not_increase(client):
    response = book(client, "Test Club", "Future Competition", "-3")
    body = text_of(response)

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in body
    assert "Réservation confirmée" not in body
    assert int(get(server.clubs, "Test Club")["points"]) <= 10
    assert_nothing_changed()


def test_booking_text_places_does_not_crash(client):
    response = book(client, "Test Club", "Future Competition", "abc")
    body = text_of(response)

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in body
    assert_nothing_changed()


def test_booking_empty_places_does_not_crash(client):
    response = book(client, "Test Club", "Future Competition", "")
    body = text_of(response)

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in body
    assert_nothing_changed()


# --- Happy path ---

def test_booking_one_place_is_accepted(client):
    response = book(client, "Test Club", "Future Competition", "1")
    body = text_of(response)

    assert response.status_code == 200
    assert "Réservation confirmée : 1 place(s) réservée(s)." in body
    assert INVALID_PLACES_ERROR not in body
    assert int(get(server.clubs, "Test Club")["points"]) == 9
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 24
