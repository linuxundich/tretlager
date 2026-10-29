import asyncio
import logging
import os

from .service import run


def main() -> None:
    logging.basicConfig(level=os.environ.get("TRETLAGER_LOG", "INFO"),
                        format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(run())


if __name__ == "__main__":
    main()
