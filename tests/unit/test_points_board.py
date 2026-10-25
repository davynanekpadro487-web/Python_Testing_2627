"""Tests unitaires : tableau public des points des clubs (route GET /points)."""
import re


def row_pattern(name, points):
    """Une ligne du tableau : nom du club suivi de ses points dans la cellule voisine."""
    return re.compile(
        rf"<td>\s*{re.escape(name)}\s*</td>\s*<td>\s*{points}\s*</td>".encode()
    )


# --- Happy paths ---

def test_points_page_is_public_and_lists_all_clubs(client):
    # Aucun appel à /showSummary : l'utilisateur n'est pas connecté.
    response = client.get("/points")

    assert response.status_code == 200
    assert row_pattern("Test Club", 10).search(response.data)
    assert row_pattern("Small Club", 4).search(response.data)
    assert row_pattern("Lucky Club", 13).search(response.data)


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

    assert response.status_code == 200
    assert b'href="/points"' in response.data


def test_welcome_page_links_to_points_page(client):
    response = client.post("/showSummary", data={"email": "test@club.com"})

    assert response.status_code == 200
    assert b'href="/points"' in response.data


# --- Sad path ---

def test_points_page_is_read_only(client):
    response = client.post("/points", data={"club": "Test Club", "points": "999"})

    assert response.status_code == 405
