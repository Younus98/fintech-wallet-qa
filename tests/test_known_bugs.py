import pytest


# ---------- Account creation ----------

def test_empty_owner_is_rejected(client):
    response = client.post("/accounts", json={"owner": ""})

    assert response.status_code == 422


def test_invalid_currency_code_is_rejected(client):
    response = client.post("/accounts", json={"owner": "Alice", "currency": "JPN"})

    assert response.status_code == 422


def test_empty_currency_is_rejected(client):
    response = client.post("/accounts", json={"owner": "Alice", "currency": ""})

    assert response.status_code == 422


def test_unknown_field_is_rejected(client):
    response = client.post("/accounts", json={"owner": "Alice", "balance": "1000.00"})

    assert response.status_code == 422


# ---------- Deposit ----------

def test_deposit_in_other_currency_is_rejected(client, make_account):
    account_id = make_account(currency="EUR")

    response = client.post(
        f"/accounts/{account_id}/deposit",
        json={"amount": "100.00", "currency": "JPY"},
    )

    assert response.status_code == 422
    assert client.get(f"/accounts/{account_id}").json()["balance"] == "0.00"


@pytest.mark.parametrize(
    "amount",
    [
        pytest.param("-500.00", id="negative",
                     marks=pytest.mark.xfail(reason="BUG-07", strict=True)),
        pytest.param("0", id="zero",
                     marks=pytest.mark.xfail(reason="BUG-08", strict=True)),
        pytest.param("10.999", id="three-decimals",
                     marks=pytest.mark.xfail(reason="BUG-09", strict=True)),
        pytest.param("1000000.01", id="above-limit",
                     marks=pytest.mark.xfail(reason="BUG-06", strict=True)),
    ],
)
def test_invalid_deposit_amount_is_rejected(client, make_account, amount):
    account_id = make_account(deposit="100.00")

    response = client.post(f"/accounts/{account_id}/deposit", json={"amount": amount})

    assert response.status_code == 422
    assert client.get(f"/accounts/{account_id}").json()["balance"] == "100.00"


# ---------- Transfer ----------

@pytest.mark.xfail(reason="BUG-10: negative transfer pulls money from receiver", strict=True)
def test_negative_transfer_is_rejected(client, make_account):
    alice = make_account("Alice", deposit="70.00")
    bob = make_account("Bob", deposit="100.00")

    response = client.post(
        "/transfers",
        json={"from_account_id": alice, "to_account_id": bob, "amount": "-50.00"},
    )

    assert response.status_code == 422
    assert client.get(f"/accounts/{alice}").json()["balance"] == "70.00"
    assert client.get(f"/accounts/{bob}").json()["balance"] == "100.00"


@pytest.mark.xfail(reason="BUG-11: transfer to same account accepted", strict=True)
def test_transfer_to_same_account_is_rejected(client, make_account):
    alice = make_account("Alice", deposit="100.00")

    response = client.post(
        "/transfers",
        json={"from_account_id": alice, "to_account_id": alice, "amount": "10.00"},
    )

    assert response.status_code == 400