import json
import config.config as config
import websockets
import asyncio
import logging
import argparse
import os
import base58

from task.task_request import request_task
from task.send_task import send_task
from compute.computation import compute_task
from clear.clear_task import clear_directory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Miner Configuration")
    parser.add_argument(
        "--MINER_POOL_IP", required=True, help="IP address of the miner pool"
    )
    parser.add_argument(
        "--MINER_POOL_PORT", required=True, type=int, help="Port of the miner pool"
    )
    parser.add_argument(
        "--WALLET_ADDRESS", required=True, help="Wallet address for the miner"
    )
    return parser.parse_args()


def ensure_directory_exists(directory_path):
    """Ensure that a directory exists; if it doesn't, create it."""
    if not os.path.exists(directory_path):
        logging.info(f"creating {directory_path}")
        os.makedirs(directory_path)


def is_valid_address(address: str) -> bool:
    try:
        _ = bytes.fromhex(address)
        return len(address) == 128
    except ValueError:
        try:
            decoded_bytes = base58.b58decode(address)
            if len(decoded_bytes) != 33:
                return False
            specifier = decoded_bytes[0]
            if specifier not in [42, 43]:
                return False
            return True
        except ValueError:

            return False
    except Exception as e:
        print(f"Error validating address: {e}")
        return False


async def start_miner():
    uri = f"ws://{config.MINER_POOL_IP}:{config.MINER_POOL_PORT}"
    logging.info(f"Connecting to miner pool at {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            # Send a ping message
            message = {
                "type": "PING",
            }

            await websocket.send(json.dumps(message))

            # Wait for a response
            response = await websocket.recv()
            if response.startswith("SUCCESS") or response.startswith("ERROR"):
                logging.info("Pool response: %s", response)

            # Request a task
            logging.info("Requesting a task from pool")
            request_response = await request_task(websocket, "request")
            print("request_response:", request_response)
            if request_response.startswith("SUCCESS") or request_response.startswith(
                "ERROR"
            ):
                logging.info("Pool response for Task: %s", request_response)

            try:
                response_data = json.loads(request_response)

                # Handle double encoded JSON if necessary
                if isinstance(response_data, str):
                    response_data = json.loads(response_data)

                if (
                    isinstance(response_data, dict)
                    and response_data.get("message_type") == "requestedTask"
                ):
                    task_id = response_data.get("id")
                    task_description = response_data.get("task")
                    task_seed = response_data.get("seed")
                    success, output = await compute_task(
                        task_id, task_description, task_seed
                    )
                    response_data = json.loads(output)
                    id = response_data.get("id")
                    outputr = response_data.get("output")

                    if success:
                        logging.info("Sending completed task to pool")
                        response = await send_task(websocket, "response", id, outputr)

                        if response.startswith("SUCCESS") or response.startswith(
                            "ERROR"
                        ):
                            logging.info(
                                "Pool response for Task submitted: %s", response
                            )
                    else:
                        logging.error("Error: Failed to compute task")
                else:
                    logging.error("Error: Response data is not a valid JSON object.")
            except json.JSONDecodeError:
                logging.error("Error: Could not decode JSON response.")
            except TypeError:
                logging.error("TypeError: The response is not in the expected format.")
            except AttributeError:
                logging.error("AttributeError: Unexpected data type.")
    except websockets.ConnectionClosedError:
        logging.error(
            "ConnectionClosedError: The websocket connection is closed unexpectedly."
        )
    except websockets.WebSocketException as e:
        logging.error(
            "WebSocketException: An error occurred with the websocket connection. Details: %s",
            e,
        )
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)


async def start_server():
    logging.info("Starting Miner...")
    try:
        while True:
            try:
                await start_miner()
            except Exception as e:
                logging.error("Miner closed due to an error: %s", e, exc_info=True)
                break
            await asyncio.sleep(config.INTERVAL)
    except KeyboardInterrupt:
        logging.info("Miner shutdown initiated by user.")
    finally:
        logging.info("Shutting down Miner...")


try:
    ensure_directory_exists("./no/")
    clear_directory("./no/")
    args = parse_args()

    if not is_valid_address(args.WALLET_ADDRESS):
        logging.error(
            "Invalid wallet address provided. Please provide a valid address."
        )
        raise ValueError(
            "Invalid wallet address provided. Please provide a valid address."
        )
    else:
        # Override config values with command-line arguments
        config.MINER_POOL_IP = args.MINER_POOL_IP
        config.MINER_POOL_PORT = args.MINER_POOL_PORT
        config.WALLET_ADDRESS = args.WALLET_ADDRESS
        asyncio.get_event_loop().run_until_complete(start_server())
except KeyboardInterrupt:
    logging.info("Miner shutdown process complete.")
