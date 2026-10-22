import pytest

import server


@pytest.fixture
def clubs_data():
    """Clubs de test, indépendants de clubs.json."""
    return [
        {"name": "Test Club", "email": "test@club.com", "points": "10"},
        {"name": "Small Club", "email": "small@club.com", "points": "4"},
    ]


@pytest.fixture
def competitions_data():
    """Compétitions de test : une future (2030) et une passée (2020)."""
    return [
        {
            "name": "Future Competition",
            "date": "2030-06-15 10:00:00",
            "numberOfPlaces": "25",
        },
        {
            "name": "Past Competition",
            "date": "2020-03-27 10:00:00",
            "numberOfPlaces": "13",
        },
    ]


@pytest.fixture(autouse=True)
def mock_data(monkeypatch, clubs_data, competitions_data):
    """Remplace server.clubs et server.competitions par des copies fraîches
    pour chaque test, afin que les tests ne s'influencent pas entre eux."""
    monkeypatch.setattr(server, "clubs", clubs_data)
    monkeypatch.setattr(server, "competitions", competitions_data)


@pytest.fixture
def app():
    server.app.config["TESTING"] = True
    return server.app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
