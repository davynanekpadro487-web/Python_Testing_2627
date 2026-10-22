"""Tests unitaires de la route /purchasePlaces (déduction des points)."""
import server


def book(client, club, competition, places):
    return client.post(
        "/purchasePlaces",
        data={"club": club, "competition": competition, "places": places},
    )


def get(collection, name):
    return next(item for item in collection if item["name"] == name)


def test_booking_deducts_club_points_and_competition_places(client):
    response = book(client, "Lucky Club", "Future Competition", "2")

    assert response.status_code == 200
    assert int(get(server.clubs, "Lucky Club")["points"]) == 11
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 23
    assert b"Points available: 11" in response.data


def test_booking_confirmation_shows_number_of_places(client):
    response = book(client, "Lucky Club", "Future Competition", "2")

    assert b"Great-booking complete! You booked 2 places." in response.data
