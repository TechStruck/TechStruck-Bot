import asyncio
import pickle
from datetime import datetime

import asyncpg

from config.common import config


async def backup():
    conn = await asyncpg.connect(str(config.database_uri))
    tables = ("users", "thanks", "guilds", "jokes")
    return {
        field: [
            dict(rec)
            for rec in await conn.fetch("SELECT * FROM {}".format(field))
        ]
        for field in tables
    }


def main():
    data = asyncio.get_event_loop().run_until_complete(backup())
    filename = "backup-{:%d-%m-%y-%H:%M}.pickle".format(datetime.now())
    with open(filename, "wb") as f:
        pickle.dump(data, f)


if __name__ == "__main__":
    main()
