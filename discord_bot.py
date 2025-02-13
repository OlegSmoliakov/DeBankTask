import json
import logging
from http import HTTPStatus

import aiohttp
import discord
from discord.ext.commands import Bot
from discord.interactions import Interaction

from api import TotalBalanceTrigger

log = logging.getLogger("DeBank")

with open("creds.json") as f:
    CREDENTIALS = json.load(f)

BOT_TOKEN = CREDENTIALS["discord"]["bot_token"]
SERVICE_URL = "http://localhost:8000"

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """Sync the bot tree."""
    await bot.tree.sync()
    log.info("Logged in %s as (ID: %s)", bot.user.name, bot.user.id)


@bot.tree.command(name="debank_total_balance")
async def debank_total_balance(interaction: Interaction, profile: str, output: str):
    """
    Request to fetch and send the total balance for a given profile to the specified output.

    Args:
        interaction (Interaction): The interaction object.
        profile (str): The profile `id` to fetch total balance.
        output (Literal["telegram", "google_sheets", "discord"]):
            The output source to send total balance.
    """

    data = TotalBalanceTrigger(output=output, profile=profile)
    response = await send_total_balance(data)
    if response:
        await interaction.response.send_message(
            f"Request to send total balance for `{profile}` with output `{output}` has been sent."
        )
    else:
        await interaction.response.send_message("Failed to send total balance.")


async def send_total_balance(data: TotalBalanceTrigger):
    """Send the total balance to the specified output."""

    url = f"{SERVICE_URL}/debank/total_balance"
    json = data.model_dump()

    async with (
        aiohttp.ClientSession() as session,
        session.post(url, json=json) as response,
    ):
        if response.status == HTTPStatus.OK:
            log.info("Total balance successfully sent to %s", data.output)
            return True

    log.error("Failed to send total balance to %s: %s", data.output, response.status)
    return None
