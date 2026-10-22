"""Tests unitaires de la route /showSummary (connexion par email)."""


def test_valid_email_shows_welcome_page(client):
    response = client.post("/showSummary", data={"email": "test@club.com"})
    assert response.status_code == 200
    assert b"Welcome, test@club.com" in response.data
    assert b"Points available: 10" in response.data


def test_unknown_email_returns_to_login_with_error(client):
    response = client.post(
        "/showSummary", data={"email": "inconnu@club.com"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Welcome to the GUDLFT Registration Portal" in response.data
    assert b"Sorry, that email was not found." in response.data


def test_empty_email_returns_to_login_with_error(client):
    response = client.post("/showSummary", data={"email": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome to the GUDLFT Registration Portal" in response.data
    assert b"Please enter your email." in response.data
