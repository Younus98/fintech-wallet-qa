from decimal import Decimal
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Mini Wallet API")

accounts = {}


class AccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    owner: str = Field(min_length=1)
    currency: Literal["EUR", "USD", "GBP", "JPY"] = "EUR"


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


class Deposit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Decimal


class Transfer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    from_account_id: str
    to_account_id: str
    amount: Decimal


class TransferResult(BaseModel):
    from_balance: Decimal
    to_balance: Decimal


@app.post("/accounts/{account_id}/deposit")
def deposit(account_id: str, data: Deposit) -> Account:
    account = get_account(account_id)
    account.balance += data.amount
    return account


@app.post("/transfers")
def transfer(data: Transfer) -> TransferResult:
    sender = get_account(data.from_account_id)
    receiver = get_account(data.to_account_id)

    if sender.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    sender.balance -= data.amount
    receiver.balance += data.amount
    return TransferResult(from_balance=sender.balance, to_balance=receiver.balance)