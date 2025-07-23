import asyncio

from template_worker.core.logger import logger
from template_worker.kafka_service.consumer import start_kafka_consumer
from template_worker.kafka_service.producer import startup_kafka, \
    shutdown_kafka


# Main entry point for running both producer and consumer
async def main():
    await startup_kafka()

    consumer_task = asyncio.create_task(start_kafka_consumer())

    try:
        await consumer_task
    except KeyboardInterrupt:
        logger.info("Shutting down due to KeyboardInterrupt")
    finally:
        await shutdown_kafka()


if __name__ == '__main__':
    asyncio.run(main())
