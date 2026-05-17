from fastapi.testclient import TestClient

from examples.json_app.main import app


def test_get_missions_no_filters() -> None:
    with TestClient(app) as client:
        response = client.get("/missions")
        assert response.status_code == 200
        assert len(response.json()) == 4


def test_get_missions_filter_commander() -> None:
    with TestClient(app) as client:
        # Test m_data__commander__eq
        response = client.get("/missions?m_data__commander__eq=Jack O'Neill")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["planet"] == "Abydos"


def test_get_missions_filter_danger_level() -> None:
    with TestClient(app) as client:
        # Test m_data__danger_level__gt
        response = client.get("/missions?m_data__danger_level__gt=6")
        assert response.status_code == 200
        data = response.json()
        # Chulak (7), Tartarus (10)
        assert len(data) == 2
        planets = [d["planet"] for d in data]
        assert "Chulak" in planets
        assert "Tartarus" in planets


def test_get_missions_global_search() -> None:
    with TestClient(app) as client:
        # Search for "Carter"
        response = client.get("/missions?q=Carter")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["planet"] == "Chulak"


def test_get_missions_sorting() -> None:
    with TestClient(app) as client:
        # Sort by danger_level ascending
        response = client.get("/missions?sort_by=m_data__danger_level")
        assert response.status_code == 200
        data = response.json()
        # 3, 5, 7, 10
        assert data[0]["data"]["danger_level"] == 3
        assert data[1]["data"]["danger_level"] == 5
        assert data[2]["data"]["danger_level"] == 7
        assert data[3]["data"]["danger_level"] == 10


def test_get_missions_date_range() -> None:
    with TestClient(app) as client:
        # Test gte and lte on dates
        response = client.get(
            "/missions?m_data__scheduled_date__gte=1998-01-01&m_data__scheduled_date__lte=2000-01-01"
        )
        assert response.status_code == 200
        data = response.json()
        # Janet (1998-05-12)
        assert len(data) == 1
        assert data[0]["planet"] == "P3X-984"


def test_get_missions_alias_check() -> None:
    with TestClient(app) as client:
        # Ensure 'planet' (alias) works instead of 'planet_name'
        response = client.get("/missions?m_planet__eq=Abydos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["planet"] == "Abydos"
