import datetime
import io
import json
import logging
import time
from http import HTTPStatus
from typing import Literal

import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core import (
    UserProtocolList,
    aggregate_parsed_protocols,
    get_protocols_total_balance,
    parse_protocol_list,
)

with open("creds.json") as f:
    CREDENTIALS: dict = json.load(f)

ACCESS_KEY = CREDENTIALS["debank_api"]["access_key"]
REQUEST_TIMEOUT = 10
DEBANK_URL = "https://pro-openapi.debank.com"
DISCORD_WEBHOOK_URL = CREDENTIALS["discord"]["webhook_url"]

app = FastAPI()
log = logging.getLogger("DeBank")


class TotalBalanceTrigger(BaseModel):
    output: Literal["telegram", "google_sheets", "discord"] = Field(example="discord")
    profile: str = Field(example="0xf7b10d603907658f690da534e9b7dbc4dab3e2d6")


class TotalBalanceResponse(BaseModel):
    message: str = Field(example="Total balance fetched and sent successfully")


@app.post(
    "/debank/total_balance",
    response_model=TotalBalanceResponse,
    summary="Get total balance from DeBank API",
)
async def get_total_balance(request: TotalBalanceTrigger):
    """Fetches the total balance from DeBank API and sends it to Telegram/Google Sheets/Discord."""

    if request.output not in ["telegram", "google_sheets", "discord"]:
        raise HTTPException(status_code=400, detail="Invalid output")

    assets_json = await fetch_all_complex_protocol_list(request.profile)
    if assets_json is None:
        raise HTTPException(status_code=500, detail="Failed to fetch total balance")

    timestamp = time.time()
    total_balance = process_total_balance(assets_json, timestamp)

    await send_output(request, total_balance)

    return {"message": "Total balance fetched and sent successfully"}


async def fetch_all_complex_protocol_list(profile: str):
    """Returns json with all used protocols for given profile."""

    headers = {"AccessKey": ACCESS_KEY}
    url = f"{DEBANK_URL}/v1/user/all_complex_protocol_list?id={profile}"

    async with (
        aiohttp.ClientSession() as session,
        session.get(url, headers=headers, timeout=REQUEST_TIMEOUT) as response,
    ):
        if response.status == HTTPStatus.OK:
            data = await response.json()
            log.debug("Response: %s", data)

            log.info("Fetched all complex protocol list from %s profile", profile)

            return data

    return None


async def send_output(trigger: TotalBalanceTrigger, total_balance: UserProtocolList):
    """Sends the total balance to the specified output."""
    if trigger.output == "telegram":
        await send_to_telegram(trigger, total_balance)
    elif trigger.output == "google_sheets":
        await send_to_google_sheets(trigger, total_balance)
    elif trigger.output == "discord":
        await send_to_discord(trigger, total_balance)


async def send_to_telegram(trigger: TotalBalanceTrigger, total_balance: UserProtocolList):
    """Sends the total balance to Telegram."""
    msg = "Telegram output is not implemented yet"
    raise NotImplementedError(msg)


async def send_to_google_sheets(trigger: TotalBalanceTrigger, total_balance: UserProtocolList):
    """Sends the total balance to Google Sheets."""
    msg = "Google Sheets output is not implemented yet"
    raise NotImplementedError(msg)


async def send_to_discord(trigger: TotalBalanceTrigger, total_balance: UserProtocolList):
    """Sends the total balance to Discord."""

    date = datetime.datetime.fromtimestamp(total_balance.timestamp, tz=datetime.UTC).strftime(
        "%Y-%m-%d, %H:%M"
    )
    data = total_balance.data.map(lambda x: f"{x:.6f}" if isinstance(x, (int, float)) else x)

    csv_file = io.StringIO()
    data.to_csv(csv_file)
    csv_file.seek(0)

    form = aiohttp.FormData()
    form.add_field("content", f"Total balance of `{trigger.profile}` profile at `{date}` UTC")
    form.add_field(
        "file",
        csv_file.getvalue(),
        filename=f"total_balance_{trigger.profile}.csv",
        content_type="text/csv",
    )

    async with (
        aiohttp.ClientSession() as session,
        session.post(DISCORD_WEBHOOK_URL, data=form) as response,
    ):
        if response.status in (HTTPStatus.NO_CONTENT, HTTPStatus.OK):
            log.info("Message sent to Discord successfully")
            return response

        log.error("Failed to send message to Discord: %s", response.status)

        return None


def process_total_balance(protocol_list: dict, timestamp: float | None = None):
    """Processes the total balance from the protocol list."""

    assets = parse_protocol_list(protocol_list)
    assets = aggregate_parsed_protocols(assets)

    total_balance = get_protocols_total_balance(assets)
    total_balance = UserProtocolList(total_balance, timestamp)

    return total_balance
