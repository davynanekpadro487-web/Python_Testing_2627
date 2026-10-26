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
    assert '<span class="points-figure">11</span>' in body
    assert "Points disponibles" in body


def test_booking_confirmation_singular_for_one_place(client):
    response = book(client, "Lucky Club", "Future Competition", "1")
    body = text_of(response)

    assert "Réservation confirmée : 1 place réservée." in body
    assert "flash-success" in body


def test_booking_confirmation_plural_for_multiple_places(client):
    response = book(client, "Lucky Club", "Future Competition", "2")
    body = text_of(response)

    assert "Réservation confirmée : 2 places réservées." in body
    assert "flash-success" in body


def test_booking_more_places_than_points_is_refused_plural(client):
    response = book(client, "Small Club", "Future Competition", "6")
    body = text_of(response)

    assert response.status_code == 200
    assert (
        "Vous n'avez pas assez de points : vous avez 4 points et avez demandé 6 places."
        in body
    )
    assert "flash-error" in body
    assert "Réservation confirmée" not in body
    assert int(get(server.clubs, "Small Club")["points"]) == 4
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 25


def test_booking_more_places_than_points_is_refused_singular(client):
    book(client, "Small Club", "Future Competition", "4")
    response = book(client, "Small Club", "Future Competition", "1")
    body = text_of(response)

    assert response.status_code == 200
    assert (
        "Vous n'avez pas assez de points : vous avez 0 point et avez demandé 1 place."
        in body
    )
    assert "(s)" not in body


def test_booking_exactly_all_points_is_accepted(client):
    response = book(client, "Small Club", "Future Competition", "4")
    body = text_of(response)

    assert "Réservation confirmée : 4 places réservées." in body
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

    assert "Réservation confirmée : 12 places réservées." in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 1
    assert int(get(server.competitions, "Future Competition")["numberOfPlaces"]) == 13


def test_booking_more_places_than_available_is_refused_plural(client):
    response = book(client, "Lucky Club", "Small Competition", "5")
    body = text_of(response)

    assert response.status_code == 200
    assert (
        "Pas assez de places disponibles : il ne reste que 3 places pour cette compétition."
        in body
    )
    assert "(s)" not in body
    assert "Réservation confirmée" not in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 13
    assert int(get(server.competitions, "Small Competition")["numberOfPlaces"]) == 3


def test_booking_more_places_than_available_is_refused_singular(client):
    book(client, "Lucky Club", "Small Competition", "2")
    response = book(client, "Lucky Club", "Small Competition", "2")
    body = text_of(response)

    assert response.status_code == 200
    assert (
        "Pas assez de places disponibles : il ne reste que 1 place pour cette compétition."
        in body
    )
    assert "(s)" not in body


def test_booking_all_remaining_places_marks_competition_full(client):
    response = book(client, "Lucky Club", "Small Competition", "3")
    body = text_of(response)

    assert "Réservation confirmée : 3 places réservées." in body
    assert int(get(server.clubs, "Lucky Club")["points"]) == 10
    assert int(get(server.competitions, "Small Competition")["numberOfPlaces"]) == 0
    assert "Complète" in body
    assert "/book/Small%20Competition/Lucky%20Club" not in body
