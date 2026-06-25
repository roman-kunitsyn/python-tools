from __future__ import annotations

import argparse
import asyncio
import logging

from aiogram import Bot
from pydantic import ValidationError

from telegram_bot.bot import build_dispatcher
from telegram_bot.config import BotSettings
from telegram_bot.services.voice_note import TelegramVoiceNoteService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Telegram voice-note bot.")
    parser.add_argument("--token", help="Telegram bot token. Defaults to TELEGRAM_BOT_TOKEN.")
    parser.add_argument(
        "--model",
        default="small",
        help="Whisper model name or path. Default: small.",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Language passed to whisper-cli. Default: auto.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Optional file for whisper-cli command logs.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print Whisper command details.",
    )
    return parser


def build_settings_from_args(args: argparse.Namespace) -> BotSettings:
    payload: dict[str, object] = {
        "model": args.model,
        "language": args.language,
        "verbose": args.verbose,
    }
    if args.token:
        payload["token"] = args.token
    if args.log_file:
        payload["log_file"] = args.log_file
    return BotSettings(**payload)


async def run_bot(settings: BotSettings) -> None:
    service = TelegramVoiceNoteService(settings)
    dispatcher = build_dispatcher(service)

    bot = Bot(token=settings.token)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        settings = build_settings_from_args(args)
        logging.basicConfig(
            level=logging.DEBUG if settings.verbose else logging.INFO,
            format="%(levelname)s %(name)s: %(message)s",
        )
        asyncio.run(run_bot(settings))
        return 0
    except ValidationError as error:
        print(f"Validation error: {error}")
        return 1
    except FileNotFoundError as error:
        print(f"Dependency not found: {error}")
        return 3
    except KeyboardInterrupt:
        return 130
