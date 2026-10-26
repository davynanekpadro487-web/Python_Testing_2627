"""Tests unitaires de la route /purchasePlaces (déduction des points)."""
import html

import server


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def book(client, club, competition, places):
    return client.post(
        "/purchasePlaces",
        data={"club": club, "competition": competition, "places": places},
    )


def get(collection, name):
    return next(item for item in collection if item["name"] == name)


def test_booking_deducts_club_points_and_competition_places(client):
    response = book(client, "Lucky Club", "Future Competition", "2")
    body = text_of(response)

    assert response.status_code == 200
    assert int(get(server.clubs, "Lucky Club")["points"]) == 11
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 23
    assert "Points disponibles : 11" in body


def test_booking_confirmation_shows_number_of_places(client):
    response = book(client, "Lucky Club", "Future Competition", "2")
    body = text_of(response)

    assert "Réservation confirmée : 2 place(s) réservée(s)." in body


def test_booking_more_places_than_points_is_refused(client):
    response = book(client, "Small Club", "Future Competition", "6")
    body = text_of(response)

    assert response.status_code == 200
    assert "Vous n'avez pas assez de points" in body
    assert "Réservation confirmée" not in body
    assert int(get(server.clubs, "Small Club")["points"]) == 4
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 25


def test_booking_exactly_all_points_is_accepted(client):
    response = book(client, "Small Club", "Future Competition", "4")
    body = text_of(response)

    assert "Réservation confirmée : 4 place(s) réservée(s)." in body
    assert int(get(server.clubs, "Small Club")["points"]) == 0
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 21


def test_booking_more_than_12_places_at_once_is_refused(client):
    response = book(client, "Lucky Club", "Future Competition", "13")
    body = text_of(response)

    assert response.status_code == 200
    assert "Vous ne pouvez pas réserver plus de 12 places par compétition" in body
    assert "Réservation confirmée" not in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 13
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 25


def test_cumulative_bookings_over_12_places_are_refused(client):
    book(client, "Lucky Club", "Future Competition", "10")
    response = book(client, "Lucky Club", "Future Competition", "3")
    body = text_of(response)

    assert "Vous ne pouvez pas réserver plus de 12 places par compétition" in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 3
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 15


def test_booking_exactly_12_places_is_accepted(client):
    response = book(client, "Lucky Club", "Future Competition", "12")
    body = text_of(response)

    assert "Réservation confirmée : 12 place(s) réservée(s)." in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 1
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 13


def test_booking_more_places_than_available_is_refused(client):
    response = book(client, "Lucky Club", "Small Competition", "5")
    body = text_of(response)

    assert response.status_code == 200
    assert "Pas assez de places disponibles" in body
    assert "Réservation confirmée" not in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 13
    assert int(get(server.competitions, "Small Competition")["numberOfPlaces"]) == 3


def test_booking_all_remaining_places_is_accepted(client):
    response = book(client, "Lucky Club", "Small Competition", "3")
    body = text_of(response)

    assert "Réservation confirmée : 3 place(s) réservée(s)." in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 10
    assert int(get(server.competitions, "Small Competition")["numberOfPlaces"]) == 0
