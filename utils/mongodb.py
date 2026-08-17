import aiosmtplib
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

import config


class MongoDB:
    def __init__(self, uri: str):
        self.client = AsyncIOMotorClient(uri)
        self.servers = self.client["servers"]
        self.users_database = self.client["usersdb"]
        self.localdb = self.client["local"]

    @property
    def guildsetting(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["guildsetting"]

    @property
    def ticketsdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["privatechannels"]

    @property
    def balancesdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.users_database["balancesdb"]

    @property
    def usersdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.users_database["usersdb"]

    @property
    def serverusers(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["serverusers"]

    @property
    def slotsdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["commendbotstatus"]

    @property
    def subdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["sub"]

    @property
    def paypal(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["paypal"]

    @property
    def timedb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["timer"]

    @property
    def statsdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["stats"]

    @property
    def blacklistdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["blacklistdb"]

    @property
    def userssubscriptions(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["userssubscriptions"]

    @property
    def sellsds(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["sellsdb"]

    @property
    def refresh(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["refresh"]

    @property
    def waitinglist(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["waitinglist"]

    @property
    def keysdb(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["keysdb"]

    @property
    def learn(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["slots_ai"]

    @property
    def slottrans(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["slottrans"]

    @property
    def invitepool(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["invite_pool"]

    @property
    def bot(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["bot"]

    @property
    def invites(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.servers["invites"]

    @property
    def oplogs(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.localdb["oplog.rs"]


def get_smtp_client() -> aiosmtplib.SMTP:
    return aiosmtplib.SMTP(
        hostname=config.SMTP_HOST,
        port=config.SMTP_PORT,
        username=config.SMTP_USER,
        password=config.SMTP_PASS,
    )


db = MongoDB(config.MONGODB_URI)

smtp = get_smtp_client()