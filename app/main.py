from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mini Wallet API")

accounts = {}


class AccountCreate(BaseModel):
    owner: str
    currency: str = "EUR"


class Account(BaseModel):
    id: str
    owner: str
    currency: str
    balance: Decimal


@app.post("/accounts", status_code=201)
def create_account(data: AccountCreate) -> Account:
    account = Account(
        id=str(uuid4()),
        owner=data.owner,
        currency=data.currency,
        balance=Decimal("0.00"),
    )
    accounts[account.id] = account
    return account


@app.get("/accounts/{account_id}")
def get_account(account_id: str) -> Account:
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    return accounts[account_id]