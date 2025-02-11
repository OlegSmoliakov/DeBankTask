import argparse
import asyncio
import logging

from api import TotalBalanceTrigger, app, fetch_total_balance, send_output
from discord_bot import BOT_TOKEN, bot

log = logging.getLogger("DeBunk")


def parse_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Fetch total balance and send it to the specified output"
    )

    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        help="The profile to fetch total balance",
        default="0xf7b10d603907658f690da534e9b7dbc4dab3e2d6",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="The output to send total balance",
        choices=["telegram", "google_sheets", "discord"],
    )

    parser.add_argument("--host", action="store_true", help="Run the server to listen for requests")

    return parser.parse_args()


async def run_discord_bot():
    """Run the Discord bot."""
    await bot.start(BOT_TOKEN)


async def run_fastapi():
    """Run the FastAPI server."""
    import uvicorn

    config = uvicorn.Config(app, host="localhost", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Run both the Discord bot and FastAPI server concurrently."""
    await asyncio.gather(run_discord_bot(), run_fastapi())


async def fetch_and_send(args: dict):
    """Fetch the total balance and send it to the specified output."""
    trigger = TotalBalanceTrigger(output=args.output, profile=args.profile)

    total_balance = await fetch_total_balance(trigger.profile)
    await send_output(trigger, total_balance)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")

    args = parse_args()

    if args.host:
        asyncio.run(main())

    if args.profile and args.output:
        asyncio.run(fetch_and_send(args))
