"""
чисто временная штука чтоб я проверил что пайплайн работает не настоящий тест)
"""
import asyncio
import logging
import os
import sys
import time
import uuid
from typing import Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import aiohttp
import clickhouse_driver
from src.core.config import get_settings
from src.core.logger import setup_logging
from src.models.metrics import ActionType


async def send_action_to_api(api_url: str) -> tuple[Any, dict[str, Any]]:
    """Send a test user action to the API.

    Args:
        api_url: URL of the API endpoint

    Returns:
        The API response and the sent action data
    """
    user_id = str(uuid.uuid4())
    movie_id = str(uuid.uuid4())

    action = {
        "user_id": user_id,
        "movie_id": movie_id,
        "action_type": ActionType.VIEW_START,
        "timestamp": time.time() * 1000,
        "metadata": {
            "duration_seconds": 3600,
            "device_type": "test_device"
        }
    }

    logging.info(f"Sending action to API: {action}")

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=action) as response:
            response_data = await response.json()
            logging.info(f"API response: {response_data}")

            if response.status != 200:
                logging.error(f"API request failed with status "
                              f"{response.status}: {response_data}")
                raise Exception(f"API request failed: {response_data}")

            return response_data, action


async def verify_data_in_clickhouse(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    action: dict,
    max_retries: int = 10,
    retry_delay: int = 2
) -> bool:
    """Verify that the action data was loaded into ClickHouse.

    Args:
        host: ClickHouse host
        port: ClickHouse port
        user: ClickHouse user
        password: ClickHouse password
        database: ClickHouse database
        action: The action data that was sent to the API
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds

    Returns:
        True if verification passed, False otherwise
    """
    client = clickhouse_driver.Client(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    user_id = action["user_id"]
    movie_id = action["movie_id"]

    for attempt in range(max_retries):
        try:
            query = f"""
            SELECT 
                user_id, 
                movie_id, 
                action_type,
                timestamp,
                duration_seconds,
                device_type
            FROM user_actions 
            WHERE user_id = '{user_id}' AND movie_id = '{movie_id}'
            """

            result = client.execute(query)

            if result:
                logging.info(f"Found action in ClickHouse: {result}")

                # Verify the data matches
                row = result[0]
                if (row[0] == user_id and
                    row[1] == movie_id and
                    row[2] == action["action_type"]):

                    logging.info("Verification successful! Data matches.")
                    return True
                else:
                    logging.error("Data mismatch")
                    logging.error(f"Expected: {action}")
                    logging.error(f"Found: {row}")
                    return False
            else:
                logging.info(f"Action not found yet,"
                             f" retrying in {retry_delay}"
                             f" seconds (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(retry_delay)
        except Exception as e:
            logging.error(f"Error querying ClickHouse: {e}")
            await asyncio.sleep(retry_delay)

    logging.error(f"Action not found in ClickHouse after {max_retries} attempts")
    return False


async def main():
    """Run the end-to-end test."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logging.info("Starting API to ClickHouse end-to-end test")

    api_url = "http://analytics_service_api:8100/api/v1/action"

    try:
        # Step 1: Send action to API
        response, action = await send_action_to_api(api_url)
        logging.info("Successfully sent action to API")

        # Step 2: Wait for ETL pipeline to process the data
        logging.info("Waiting for ETL pipeline to process the data...")
        await asyncio.sleep(15)

        # Step 3: Verify data in ClickHouse
        result = await verify_data_in_clickhouse(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            user=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database,
            action=action,
            max_retries=15,
            retry_delay=3
        )

        if result:
            logging.info("End-to-end test passed! The full pipeline is working correctly.")
        else:
            logging.error("End-to-end test failed! "
                          "Data was not properly transferred to ClickHouse.")

    except Exception as e:
        logging.error(f"Test failed with error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
