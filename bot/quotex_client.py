import logging
import time

from pyquotex.stable_api import Quotex

logger = logging.getLogger(__name__)


class QuotexClient:
    def __init__(self, email, password, account_type="demo"):
        self.email = email
        self.password = password
        self.account_type = account_type

        self.client = None
        self.connected = False

    async def connect(self):
        """Connect to Quotex."""

        try:
            self.client = Quotex(
                email=self.email,
                password=self.password,
                lang="en"
            )

            connected = await self.client.connect()

            if connected:
                self.connected = True
                logger.info("Connected to Quotex.")
                return True

            return False

        except Exception as e:
            logger.exception(e)
            return False

    async def disconnect(self):
        """Disconnect from Quotex."""

        try:
            if self.client:
                await self.client.close()

            self.connected = False

        except Exception as e:
            logger.exception(e)

    async def get_balance(self):
        """Return account balance."""

        if not self.connected:
            return None

        try:
            return await self.client.get_balance()

        except Exception as e:
            logger.exception(e)
            return None

    async def get_candles(
        self,
        asset="EURUSD_otc",
        timeframe=60,
        count=200,
    ):
        """
        Download historical candles.
        """

        if not self.connected:
            return []

        try:
            candles = await self.client.get_candles(
                asset=asset,
                end_from_time=time.time(),
                offset=count,
                period=timeframe,
            )

            if candles is None:
                return []

            return candles

        except Exception as e:
            logger.exception(e)
            return []