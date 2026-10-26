"""Tests unitaires : tableau public des points des clubs (route GET /points)."""
import html
import re

import server


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def row_pattern(name, points):
    """Une ligne du tableau : nom du club suivi de ses points dans la cellule voisine."""
    return re.compile(
        rf"<td>\s*{re.escape(name)}\s*</td>\s*<td>\s*{points}\s*</td>".encode()
    )


# --- Happy paths ---

def test_points_page_is_public_and_lists_all_clubs(client):
    # Aucun appel à /showSummary : l'utilisateur n'est pas connecté.
    response = client.get("/points")
    body = text_of(response)

    assert response.status_code == 200
    assert "Points des clubs" in body
    assert row_pattern("Test Club", 10).search(response.data)
    assert row_pattern("Small Club", 4).search(response.data)
    assert row_pattern("Lucky Club", 13).search(response.data)
    assert "Retour à l'accueil" in body


def test_points_page_sorts_clubs_descending_without_mutating_memory(client):
    original_names = [c["name"] for c in server.clubs]

    response = client.get("/points")
    body = text_of(response)

    assert response.status_code == 200
    lucky_pos = body.index("Lucky Club")
    test_pos = body.index("Test Club")
    small_pos = body.index("Small Club")
    assert lucky_pos < test_pos < small_pos
    assert [c["name"] for c in server.clubs] == original_names


def test_points_page_shows_updated_points_after_booking(client):
    client.post(
        "/purchasePlaces",
        data={"club": "Lucky Club", "competition": "Future Competition", "places": "2"},
    )

    response = client.get("/points")

    assert response.status_code == 200
    assert row_pattern("Lucky Club", 11).search(response.data)
    assert not row_pattern("Lucky Club", 13).search(response.data)


def test_index_page_links_to_points_page(client):
    response = client.get("/")
    body = text_of(response)

    assert response.status_code == 200
    assert 'href="/points"' in body
    assert "Voir les points des clubs" in body


def test_welcome_page_links_to_points_page(client):
    response = client.post("/showSummary", data={"email": "test@club.com"})
    body = text_of(response)

    assert response.status_code == 200
    assert 'href="/points"' in body
    assert "Voir les points des clubs" in body


# --- Sad path ---

def test_points_page_is_read_only(client):
    response = client.post("/points", data={"club": "Test Club", "points": "999"})

    assert response.status_code == 405
