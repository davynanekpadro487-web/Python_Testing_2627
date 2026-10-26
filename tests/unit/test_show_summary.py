"""Tests unitaires de la route /showSummary (connexion par email) et du filtre date_fr."""
import html

import server


def text_of(response):
    return html.unescape(response.data.decode("utf-8"))


def test_valid_email_shows_welcome_page(client):
    response = client.post("/showSummary", data={"email": "test@club.com"})
    body = text_of(response)
    assert response.status_code == 200
    assert "Bienvenue, test@club.com" in body
    assert '<span class="points-figure">10</span>' in body
    assert "Points disponibles" in body
    assert "Places restantes : 25" in body
    assert "Se déconnecter" in body


def test_unknown_email_returns_to_login_with_error(client):
    response = client.post(
        "/showSummary", data={"email": "inconnu@club.com"}, follow_redirects=True
    )
    body = text_of(response)
    assert response.status_code == 200
    assert "Bienvenue sur le portail de réservation GUDLFT" in body
    assert "Désolé, cette adresse e-mail est introuvable." in body
    assert "flash-error" in body


def test_empty_email_returns_to_login_with_error(client):
    response = client.post("/showSummary", data={"email": ""}, follow_redirects=True)
    body = text_of(response)
    assert response.status_code == 200
    assert "Bienvenue sur le portail de réservation GUDLFT" in body
    assert "Veuillez saisir votre adresse e-mail." in body
    assert "flash-error" in body


def test_date_fr_formats_valid_datetime():
    assert server.date_fr("2020-03-27 10:00:00") == "27 mars 2020 à 10h00"
    assert server.date_fr("2030-06-15 13:30:00") == "15 juin 2030 à 13h30"


def test_date_fr_returns_malformed_date_without_crash():
    assert server.date_fr("date-invalide") == "date-invalide"
    assert server.date_fr("") == ""


def test_welcome_page_uses_date_fr_filter(client):
    response = client.post("/showSummary", data={"email": "test@club.com"})
    body = text_of(response)
    assert "15 juin 2030 à 10h00" in body
    assert "27 mars 2020 à 10h00" in body


def test_stylesheet_is_loaded_on_all_pages(client):
    pages = [
        client.get("/"),
        client.post("/showSummary", data={"email": "test@club.com"}),
        client.get("/book/Future Competition/Test Club"),
        client.get("/points"),
    ]
    for res in pages:
        body = text_of(res)
        assert res.status_code == 200
        assert "/static/css/style.css" in body
        assert "GUDLFT — Portail des secrétariats de clubs" in body
