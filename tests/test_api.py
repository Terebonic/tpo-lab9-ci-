"""API-тесты DummyJSON Users API на requests + pytest — повторяют тесты Postman-коллекции."""
import re

import pytest
import requests

pytestmark = pytest.mark.api  # запускаются отдельной задачей CI

BASE_URL = "https://dummyjson.com"
TIMEOUT = 10
MAX_TIME = 1.5  # секунды, как в Postman (< 1500 мс)


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers["Content-Type"] = "application/json"
    yield s
    s.close()


CREATE_PAYLOAD = {"firstName": "Sergey", "lastName": "Matyushkin", "age": 21, "email": "s.matyushkin@example.com",
                  "company": {"title": "QA Engineer", "department": "Testing"}}
UPDATE_PAYLOAD = {"lastName": "Johnson-Smith", "email": "emily.new@example.com"}


# один запрос на группу тестов
@pytest.fixture(scope="module")
def get_resp(session):
    return session.get(f"{BASE_URL}/users/1", timeout=TIMEOUT)


@pytest.fixture(scope="module")
def post_resp(session):
    return session.post(f"{BASE_URL}/users/add", json=CREATE_PAYLOAD, timeout=TIMEOUT)


@pytest.fixture(scope="module")
def put_resp(session):
    return session.put(f"{BASE_URL}/users/1", json=UPDATE_PAYLOAD, timeout=TIMEOUT)


# ---------------- GET ----------------
class TestGetUser:
    @pytest.fixture
    def resp(self, get_resp):
        return get_resp

    def test_status_200(self, resp):
        assert resp.status_code == 200

    def test_response_time(self, resp):
        assert resp.elapsed.total_seconds() < MAX_TIME

    def test_content_type_json(self, resp):
        assert "application/json" in resp.headers["Content-Type"]

    def test_structure(self, resp):
        u = resp.json()
        for key in ("id", "firstName", "lastName", "email", "age", "address", "company"):
            assert key in u, f"нет поля {key}"
        assert {"city", "country"} <= u["address"].keys()

    def test_types(self, resp):
        u = resp.json()
        assert isinstance(u["id"], int) and isinstance(u["age"], int) and u["age"] >= 0
        assert isinstance(u["firstName"], str) and re.fullmatch(r"[^@\s]+@[^@\s]+", u["email"])

    def test_values(self, resp):
        u = resp.json()
        assert (u["id"], u["firstName"], u["lastName"]) == (1, "Emily", "Johnson")


# ---------------- POST ----------------
class TestCreateUser:
    payload = CREATE_PAYLOAD

    @pytest.fixture
    def resp(self, post_resp):
        return post_resp

    def test_status_201(self, resp):
        assert resp.status_code == 201

    def test_response_time(self, resp):
        assert resp.elapsed.total_seconds() < MAX_TIME

    def test_returns_new_id(self, resp):
        assert isinstance(resp.json()["id"], int) and resp.json()["id"] > 0

    @pytest.mark.parametrize("field", ["firstName", "lastName", "age", "email"])
    def test_fields_echoed(self, resp, field):
        assert resp.json()[field] == self.payload[field]

    def test_nested_company(self, resp):
        assert resp.json()["company"]["title"] == "QA Engineer"


# ---------------- PUT ----------------
class TestUpdateUser:
    @pytest.fixture
    def resp(self, put_resp):
        return put_resp

    def test_status_200(self, resp):
        assert resp.status_code == 200

    def test_id_unchanged(self, resp):
        assert resp.json()["id"] == 1

    def test_updated_fields(self, resp):
        u = resp.json()
        assert u["lastName"] == "Johnson-Smith" and u["email"] == "emily.new@example.com"

    def test_other_fields_kept(self, resp):
        u = resp.json()
        assert u["firstName"] == "Emily" and u["age"] == 29


# ---------------- негативный ----------------
@pytest.mark.parametrize("user_id", [0, 100000])
def test_user_not_found(session, user_id):
    resp = session.get(f"{BASE_URL}/users/{user_id}", timeout=TIMEOUT)
    assert resp.status_code == 404
    assert resp.json()["message"] == f"User with id '{user_id}' not found"
