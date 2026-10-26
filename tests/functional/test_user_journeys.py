"""Tests fonctionnels simulant des parcours utilisateurs complets avec le client Flask."""
import html
import re


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def row_pattern(name, points):
    """Vérifie la présence d'un club et de ses points dans le tableau /points."""
    return re.compile(
        rf"<td>\s*{re.escape(name)}\s*</td>\s*<td>\s*{points}\s*</td>".encode()
    )


def test_nominal_secretary_journey(client):
    """Parcours nominal : accueil -> connexion -> choix d'une compétition ->
    réservation -> confirmation -> consultation de /points -> déconnexion."""
    home_response = client.get("/")
    assert home_response.status_code == 200
    assert "Bienvenue sur le portail de réservation GUDLFT" in text_of(home_response)

    login_response = client.post("/showSummary", data={"email": "test@club.com"})
    login_body = text_of(login_response)
    assert login_response.status_code == 200
    assert "Bienvenue, test@club.com" in login_body
    assert '<span class="points-figure">10</span>' in login_body

    book_page = client.get("/book/Future Competition/Test Club")
    book_body = text_of(book_page)
    assert book_page.status_code == 200
    assert "<h2>Future Competition</h2>" in book_body
    assert "Places restantes : 25" in book_body

    purchase_response = client.post(
        "/purchasePlaces",
        data={
            "club": "Test Club",
            "competition": "Future Competition",
            "places": "3",
        },
    )
    purchase_body = text_of(purchase_response)
    assert purchase_response.status_code == 200
    assert "Réservation confirmée : 3 places réservées." in purchase_body
    assert '<span class="points-figure">7</span>' in purchase_body
    assert "Places restantes : 22" in purchase_body

    points_response = client.get("/points")
    assert points_response.status_code == 200
    assert "Points des clubs" in text_of(points_response)
    assert row_pattern("Test Club", 7).search(points_response.data)

    logout_response = client.get("/logout", follow_redirects=True)
    assert logout_response.status_code == 200
    assert "Bienvenue sur le portail de réservation GUDLFT" in text_of(logout_response)


def test_error_journey_unknown_email_invalid_places_then_valid_booking(client):
    """Parcours avec erreurs : email inconnu -> bon email -> saisie 'abc' ->
    13 places -> réservation valide."""
    bad_login = client.post(
        "/showSummary",
        data={"email": "unknown@club.com"},
        follow_redirects=True,
    )
    assert bad_login.status_code == 200
    assert "Désolé, cette adresse e-mail est introuvable." in text_of(bad_login)

    valid_login = client.post("/showSummary", data={"email": "lucky@club.com"})
    assert valid_login.status_code == 200
    assert "Bienvenue, lucky@club.com" in text_of(valid_login)

    client.get("/book/Future Competition/Lucky Club")

    text_booking = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Future Competition",
            "places": "abc",
        },
    )
    assert text_booking.status_code == 200
    assert "Veuillez saisir un nombre de places valide" in text_of(text_booking)

    over_limit_booking = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Future Competition",
            "places": "13",
        },
    )
    assert over_limit_booking.status_code == 200
    assert (
        "Vous ne pouvez pas réserver plus de 12 places par compétition"
        in text_of(over_limit_booking)
    )

    valid_booking = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Future Competition",
            "places": "5",
        },
    )
    valid_body = text_of(valid_booking)
    assert valid_booking.status_code == 200
    assert "Réservation confirmée : 5 places réservées." in valid_body
    assert '<span class="points-figure">8</span>' in valid_body


def test_unauthenticated_visitor_browses_points_board(client):
    """Visiteur non connecté qui consulte /points depuis la page d'accueil."""
    home_response = client.get("/")
    assert home_response.status_code == 200
    assert 'href="/points"' in text_of(home_response)

    points_response = client.get("/points")
    points_body = text_of(points_response)
    assert points_response.status_code == 200
    assert "Points des clubs" in points_body
    assert row_pattern("Test Club", 10).search(points_response.data)
    assert row_pattern("Small Club", 4).search(points_response.data)
    assert row_pattern("Lucky Club", 13).search(points_response.data)
    assert "Retour à l'accueil" in points_body

    back_home = client.get("/")
    assert back_home.status_code == 200


def test_secretary_past_competition_error_then_valid_future_booking(client):
    """Tentative de réservation sur une compétition passée puis achat sur une future."""
    client.post("/showSummary", data={"email": "test@club.com"})

    past_attempt = client.get("/book/Past Competition/Test Club")
    assert past_attempt.status_code == 200
    assert (
        "Cette compétition a déjà eu lieu, la réservation n'est pas possible."
        in text_of(past_attempt)
    )

    future_page = client.get("/book/Future Competition/Test Club")
    assert future_page.status_code == 200
    assert "<form" in text_of(future_page)

    valid_purchase = client.post(
        "/purchasePlaces",
        data={
            "club": "Test Club",
            "competition": "Future Competition",
            "places": "2",
        },
    )
    assert "Réservation confirmée : 2 places réservées." in text_of(valid_purchase)

    logout_response = client.get("/logout", follow_redirects=True)
    assert logout_response.status_code == 200


def test_two_secretaries_competing_for_last_places_journey(client):
    """Deux secrétaires réservent successivement les dernières places d'une compétition."""
    client.post("/showSummary", data={"email": "lucky@club.com"})
    first_purchase = client.post(
        "/purchasePlaces",
        data={
            "club": "Lucky Club",
            "competition": "Small Competition",
            "places": "2",
        },
    )
    assert "Réservation confirmée : 2 places réservées." in text_of(first_purchase)
    client.get("/logout", follow_redirects=True)

    client.post("/showSummary", data={"email": "small@club.com"})
    too_many = client.post(
        "/purchasePlaces",
        data={
            "club": "Small Club",
            "competition": "Small Competition",
            "places": "2",
        },
    )
    assert (
        "Pas assez de places disponibles : il ne reste que 1 place pour cette compétition."
        in text_of(too_many)
    )

    last_place = client.post(
        "/purchasePlaces",
        data={
            "club": "Small Club",
            "competition": "Small Competition",
            "places": "1",
        },
    )
    last_body = text_of(last_place)
    assert "Réservation confirmée : 1 place réservée." in last_body
    assert "Places restantes : 0" in last_body
    assert "Complète" in last_body
