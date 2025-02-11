import json
import logging
from http import HTTPStatus
from typing import Literal

import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

with open("creds.json") as f:
    CREDENTIALS: dict = json.load(f)

ACCESS_KEY = CREDENTIALS["debunk_api"]["access_key"]
REQUEST_TIMEOUT = 10
DEBUNK_URL = "https://pro-openapi.debank.com"
DISCORD_WEBHOOK_URL = CREDENTIALS["discord"]["webhook_url"]

app = FastAPI()
log = logging.getLogger("DeBunk")


class TotalBalanceTrigger(BaseModel):
    output: Literal["telegram", "google_sheets", "discord"] = Field(example="discord")
    profile: str = Field(example="0xf7b10d603907658f690da534e9b7dbc4dab3e2d6")


class TotalBalanceResponse(BaseModel):
    message: str = Field(example="Total balance fetched and sent successfully")


@app.post(
    "/debunk/total_balance",
    response_model=TotalBalanceResponse,
    summary="Get total balance from DeBunk API",
)
async def get_total_balance(request: TotalBalanceTrigger):
    """Fetches the total balance from Debunk API and sends it to Telegram/Google Sheets/Discord."""

    if request.output not in ["telegram", "google_sheets", "discord"]:
        raise HTTPException(status_code=400, detail="Invalid output")

    total_balance = await fetch_total_balance(request.profile)

    if total_balance is not None:
        await send_output(request, total_balance)
        return {"message": "Total balance fetched and sent successfully"}

    raise HTTPException(status_code=500, detail="Failed to fetch total balance")


async def fetch_total_balance(profile: str):
    """Returns the total balance from given profile."""

    headers = {"AccessKey": ACCESS_KEY}
    url = f"{DEBUNK_URL}/v1/user/total_balance?id={profile}"

    async with (
        aiohttp.ClientSession() as session,
        session.get(url, headers=headers, timeout=REQUEST_TIMEOUT) as response,
    ):
        if response.status == HTTPStatus.OK:
            data = await response.json()
            log.debug("Response: %s", data)

            total_balance: float = data["total_usd_value"]
            log.info("Fetched total balance: %s from %s", total_balance, profile)

            return total_balance

    return None


async def send_output(trigger: TotalBalanceTrigger, total_balance: float):
    """Sends the total balance to the specified output."""
    if trigger.output == "telegram":
        await send_to_telegram(trigger, total_balance)
    elif trigger.output == "google_sheets":
        await send_to_google_sheets(trigger, total_balance)
    elif trigger.output == "discord":
        await send_to_discord(trigger, total_balance)


async def send_to_telegram(trigger: TotalBalanceTrigger, total_balance: float):
    """Sends the total balance to Telegram."""


async def send_to_google_sheets(trigger: TotalBalanceTrigger, total_balance: float):
    """Sends the total balance to Google Sheets."""


async def send_to_discord(trigger: TotalBalanceTrigger, total_balance: float):
    """Sends the total balance to Discord."""
    message = {
        "content": f"The total balance for profile: {trigger.profile} is ${total_balance:.2f}"
    }

    async with (
        aiohttp.ClientSession() as session,
        session.post(DISCORD_WEBHOOK_URL, json=message) as response,
    ):
        if response.status == HTTPStatus.NO_CONTENT:
            log.info("Message sent to Discord successfully")
        else:
            log.error("Failed to send message to Discord: %s", response.status)
