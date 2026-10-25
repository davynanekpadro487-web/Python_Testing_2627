"""Tests unitaires : validation du nombre de places saisi dans /purchasePlaces."""
import server


INVALID_PLACES_ERROR = b"Please enter a valid number of places (a whole number greater than 0)."


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

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in response.data
    assert b"Great-booking complete!" not in response.data
    assert_nothing_changed()


def test_booking_negative_places_is_refused_and_points_do_not_increase(client):
    response = book(client, "Test Club", "Future Competition", "-3")

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in response.data
    assert b"Great-booking complete!" not in response.data
    assert int(get(server.clubs, "Test Club")["points"]) <= 10
    assert_nothing_changed()


def test_booking_text_places_does_not_crash(client):
    response = book(client, "Test Club", "Future Competition", "abc")

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in response.data
    assert_nothing_changed()


def test_booking_empty_places_does_not_crash(client):
    response = book(client, "Test Club", "Future Competition", "")

    assert response.status_code == 200
    assert INVALID_PLACES_ERROR in response.data
    assert_nothing_changed()


# --- Happy path ---

def test_booking_one_place_is_accepted(client):
    response = book(client, "Test Club", "Future Competition", "1")

    assert response.status_code == 200
    assert b"Great-booking complete! You booked 1 places." in response.data
    assert INVALID_PLACES_ERROR not in response.data
    assert int(get(server.clubs, "Test Club")["points"]) == 9
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 24
