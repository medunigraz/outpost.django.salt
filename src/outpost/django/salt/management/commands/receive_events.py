import sys
import json
import re
import asyncio
import aiohttp
import concurrent
import logging

from purl import URL
from django.core.management.base import BaseCommand

from ...conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Watch for events on the Saltstack bus."
    token = None
    token_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    url = URL(settings.SALT_MANAGEMENT_URL)

    def add_arguments(self, parser):
        pass

    async def get_token(self, session):
        data = {
            "username": settings.SALT_MANAGEMENT_USER,
            "password": settings.SALT_MANAGEMENT_PASSWORD,
            "eauth": "rest",
        }
        headers = {"content-type": "application/json"}
        url = self.url.add_path_segment("login").as_string()
        logger.debug(f"Fetching new token from {url}")
        async with session.post(url, json=data, headers=headers) as response:
            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError as e:
                logger.warn(f"Could not fetch new token: {e}")
                self.token_event.clear()
                self.token = None
                self.loop.call_later(
                    settings.SALT_EVENTS_RETRY, self.get_token, (session,)
                )
                return
            response = await response.json()
            returned = next(response.get("return").__iter__())
            self.token = returned.get("token")
            logger.debug(f"Got new token: {self.token}")
            if not self.token_event.is_set():
                logger.debug("Setting token event")
                self.token_event.set()
            lifetime = returned.get("expire") - returned.get("start")
            self.loop.call_later(lifetime - 60, self.get_token, (session,))

    async def run(self):
        pattern = re.compile(r"^(?P<type>\w+): (?P<data>.*)$")
        url = self.url.add_path_segment("events").as_string()
        async with aiohttp.ClientSession() as session:
            await self.get_token(session)
            while True:
                logger.debug("Waiting for token")
                await self.token_event.wait()
                try:
                    headers = {"X-Auth-Token": self.token}
                    async with session.get(url, headers=headers) as stream:
                        try:
                            stream.raise_for_status()
                        except aiohttp.ClientResponseError as e:
                            logger.warn(f"Could not connect to event bus: {e}")
                            continue
                        async for line in stream.content:
                            raw = line.decode("utf-8")
                            matches = pattern.match(raw)
                            if not matches:
                                logger.debug(f"Pattern does not match: {raw}")
                                continue
                            groups = matches.groupdict()
                            t = groups.get("type")
                            logger.debug(f"Received message of type {t}")
                            if t == "data":
                                json.loads(matches.groupdict().get("data"))
                                # TODO: Process message

                except (
                    aiohttp.client_exceptions.ClientPayloadError,
                    concurrent.futures._base.TimeoutError,
                ):
                    pass

    def handle(self, *args, **options):
        try:
            self.loop.run_until_complete(self.run())
        except OSError as exc:
            sys.exit("Error starting server: " + str(exc))
