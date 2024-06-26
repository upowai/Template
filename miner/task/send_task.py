import json
import config.config as config
import logging
import websockets

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


async def send_task(websocket, message_type, task_id, output):
    message = {
        "type": message_type,
        "id": task_id,
        "output": output,
        "wallet_address": config.WALLET_ADDRESS,
    }

    try:
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        return response

    except websockets.ConnectionClosedError as e:
        logging.error("Websocket connection closed unexpectedly: %s", e)
    except websockets.WebSocketException as e:
        logging.error("Websocket error: %s", e)
    except Exception as e:
        logging.error("Unexpected error: %s", e)

    return None
