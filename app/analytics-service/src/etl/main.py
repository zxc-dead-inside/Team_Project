import asyncio
import logging
import signal
import sys

from src.core.config import get_settings
from src.core.logger import setup_logging
from src.etl.container import ETLContainer


async def main():
    """Run the ETL service."""
    settings = get_settings()
    setup_logging(settings.log_level)
    container = ETLContainer()
    ETLContainer.init_config_from_settings(container, settings)
    etl_service = container.etl_service()
    loop = asyncio.get_running_loop()
    
    def signal_handler():
        logging.info("Received shutdown signal")
        asyncio.create_task(shutdown(etl_service))
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        logging.info(f"Starting ETL service in {settings.environment} mode")
        await etl_service.start()

        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logging.error(f"Error in ETL service: {e}")
        await shutdown(etl_service)
        sys.exit(1)


async def shutdown(etl_service):
    """Shutdown the ETL service gracefully."""
    logging.info("Shutting down ETL service")
    await etl_service.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    logging.info("ETL service shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
