import pytest
from fastapi.testclient import TestClient

from app.main import app, accounts


@pytest.fixture
def client():
    accounts.clear()
    return TestClient(app)


@pytest.fixture
def make_account(client):
    def _make_account(owner="Alice", currency="EUR", deposit=None):
        response = client.post("/accounts", json={"owner": owner, "currency": currency})
        account_id = response.json()["id"]
        if deposit is not None:
            client.post(f"/accounts/{account_id}/deposit", json={"amount": deposit})
        return account_id

    return _make_account