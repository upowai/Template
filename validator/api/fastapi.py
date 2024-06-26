from fastapi import FastAPI, HTTPException, Query, Request, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import hashlib
from pydantic import BaseModel


from database.db_requests import (
    get_balance_from_wallet,
    get_balance_entityOwners,
    deduct_balance_from_wallet,
    deduct_balance_from_entityOwners,
)
from utils.layout import base

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResultSubmission(BaseModel):
    nonce: int
    challenge_id: str
    result_hash: str
    wallet_address: str


class Challenge(BaseModel):
    time: str
    previous_hash: str
    difficulty: int
    target: str


class DeductBalanceRequest(BaseModel):
    wallet_address: str
    amount_to_deduct: float


class DeductBalancePool(BaseModel):
    amount_to_deduct: float


class SubmitData(BaseModel):
    index: int
    nonce: int
    result_hash: str
    wallet_address: str
    time: str
    previous_hash: str
    difficulty: int
    target: str


@app.get("/get_balance/")
@limiter.limit(base["RATE_LIMIT"]["RATE_LIMIT1"])
async def get_balance(request: Request, wallet_address: str):
    if not wallet_address:
        raise HTTPException(status_code=400, detail="Wallet address must be provided")

    balance = get_balance_from_wallet(wallet_address)
    if isinstance(balance, str) and balance.startswith("Error"):

        raise HTTPException(
            status_code=404 if "not found" in balance else 400, detail=balance
        )

    return {"balance": balance}


@app.get("/get_balance_entityOwners/")
@limiter.limit(base["RATE_LIMIT"]["RATE_LIMIT1"])
async def poolowner_get_balance(request: Request):
    balance = get_balance_entityOwners()
    if isinstance(balance, str) and balance.startswith("Error"):

        raise HTTPException(
            status_code=404 if "not found" in balance else 400, detail=balance
        )
    return {"balance": balance}


@app.post("/deduct_balance/")
@limiter.limit(base["RATE_LIMIT"]["RATE_LIMIT2"])
async def deduct_balance(
    request: Request,
    deduct_request: DeductBalanceRequest,
):
    result, response = deduct_balance_from_wallet(
        deduct_request.wallet_address, deduct_request.amount_to_deduct
    )
    if result is None:
        raise HTTPException(status_code=400, detail=response)

    return {"message": f"Amount deducted successfully: {response}"}


@app.post("/entityOwners_deduct_balance/")
@limiter.limit(base["RATE_LIMIT"]["RATE_LIMIT1"])
async def valowner_deduct_balance(
    request: Request,
    deduct_request: DeductBalancePool,
):
    result, response = deduct_balance_from_entityOwners(deduct_request.amount_to_deduct)
    if result is None:
        raise HTTPException(status_code=400, detail=response)

    return {"message": f"Amount deducted successfully: {response}"}


# @app.get("/latestwithdraws/")
# @limiter.limit(base["RATE_LIMIT"]["RATE_LIMIT1"])
# async def latest_withdraws(request: Request, wallet_address: str):
#     if not wallet_address:
#         raise HTTPException(status_code=400, detail="Wallet address must be provided")

#     result = get_miner_TransactionsPushed(wallet_address)

#     if not result.get("success", False):
#         message = result.get("message", "An unexpected error occurred")
#         status_code = 404 if "No details found" in message else 500
#         raise HTTPException(status_code=status_code, detail=message)
#     return result.get("data", {})
