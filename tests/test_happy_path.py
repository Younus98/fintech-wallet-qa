def test_create_account_returns_201_and_zero_balance(client):
    response = client.post("/accounts", json={"owner": "Alice"})

    assert response.status_code == 201
    body = response.json()
    assert body["owner"] == "Alice"
    assert body["currency"] == "EUR"
    assert body["balance"] == "0.00"
    assert body["id"]


def test_get_unknown_account_returns_404(client):
    response = client.get("/accounts/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"


def test_deposit_increases_balance(client, make_account):
    account_id = make_account()

    response = client.post(f"/accounts/{account_id}/deposit", json={"amount": "100.00"})

    assert response.status_code == 200
    assert response.json()["balance"] == "100.00"


def test_decimal_amounts_add_up_exactly(client, make_account):
    account_id = make_account()

    client.post(f"/accounts/{account_id}/deposit", json={"amount": "0.10"})
    response = client.post(f"/accounts/{account_id}/deposit", json={"amount": "0.20"})

    assert response.json()["balance"] == "0.30"


def test_transfer_moves_money_between_accounts(client, make_account):
    alice = make_account("Alice", deposit="100.00")
    bob = make_account("Bob")

    response = client.post(
        "/transfers",
        json={"from_account_id": alice, "to_account_id": bob, "amount": "30.00"},
    )

    assert response.status_code == 200
    assert response.json() == {"from_balance": "70.00", "to_balance": "30.00"}


def test_transfer_with_insufficient_funds_is_rejected(client, make_account):
    alice = make_account("Alice", deposit="50.00")
    bob = make_account("Bob")

    response = client.post(
        "/transfers",
        json={"from_account_id": alice, "to_account_id": bob, "amount": "100.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"
    assert client.get(f"/accounts/{alice}").json()["balance"] == "50.00"
    assert client.get(f"/accounts/{bob}").json()["balance"] == "0.00"