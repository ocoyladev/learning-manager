import time

import structlog

logger = structlog.get_logger(__name__)


def run() -> None:
    logger.info("worker_started")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    run()
