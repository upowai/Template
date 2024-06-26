from faker import Faker
from database.mongodb import storeTasks, poolTasks, iNodeTask
from datetime import datetime, timedelta
import uuid_utils as uuid
import json
from pymongo.errors import PyMongoError
import math
import logging


faker = Faker()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


async def handle_pool_response(val_id, task_info, pool_wallet, pool_ip, pool_port):
    try:
        # Check if val_id already exists
        existing_document = storeTasks.find_one({"val_id": val_id})
        if existing_document:
            return (
                False,
                f"Error: validation task with val_id: {val_id} already exists.",
            )

        # Prepare task_info to include additional fields
        formatted_task_info = [
            {
                "task": task.get("task"),
                "wallet_address": task.get("wallet"),
                "time": datetime.fromisoformat(task.get("time")),
                "retrieve_id": task.get("retrieve_id"),
                "status": task.get("status"),
                "type": task.get("type"),
            }
            for task in task_info
        ]

        # Insert document
        storeTasks.insert_one(
            {
                "val_id": val_id,
                "pool_wallet": pool_wallet,
                "pool_ip": pool_ip,
                "pool_port": pool_port,
                "task_info": formatted_task_info,
            }
        )

        return True, f"Document created with val_id: {val_id}."

    except Exception as e:
        return False, f"An error occurred in handle_response: {str(e)}"


def validate_tasks():
    try:
        # Find the first document in the storeTasks collection
        store_task = storeTasks.find_one()

        if store_task:
            # Extract the necessary info
            val_id = store_task.get("val_id")
            pool_wallet = store_task.get("pool_wallet")
            pool_ip = store_task.get("pool_ip")
            pool_port = store_task.get("pool_port")

            # Get unique wallets
            wallet_info = store_task.get("task_info", [])
            unique_wallets = []
            seen_wallets = set()

            for task in wallet_info:
                wallet = task.get("wallet_address")
                if wallet not in seen_wallets:
                    seen_wallets.add(wallet)
                    unique_wallets.append(wallet)

            """
            here you need to desgin your own validation logic. 
            """

            # Prepare document for poolTasks collection
            pool_task = {
                "val_id": val_id,
                "pool_ip": pool_ip,
                "pool_port": pool_port,
                "tasks": [
                    {"wallet_address": wallet, "np": i + 1}
                    for i, wallet in enumerate(unique_wallets)
                ],
            }

            # Insert the document into poolTasks collection
            result = poolTasks.insert_one(pool_task)

            if result.acknowledged:
                # Delete the store_task from storeTasks collection
                storeTasks.delete_one({"_id": store_task["_id"]})

                # Prepare document for iNodeTask collection
                inode_task = {"val_id": val_id, "pool_wallet": pool_wallet}

                # Insert the document into iNodeTask collection
                iNodeTask.insert_one(inode_task)

                return (
                    True,
                    "Document successfully moved from storeTasks to poolTasks, deleted from storeTasks, and added to iNodeTask.",
                )
            else:
                return False, "Failed to insert document into poolTasks."

        else:
            return False, "No Task found to validate"

    except PyMongoError as e:
        return False, f"An error occurred while accessing MongoDB: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred in validate_tasks: {e}"


def find_inode_task():
    try:
        document = iNodeTask.find_one()

        if document:
            return True, document
        else:
            return False, "No task found in iNodeTask."

    except PyMongoError as e:
        return False, f"An error occurred while accessing MongoDB: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred in find_inode_task: {e}"


def find_pool_task():
    try:
        document = poolTasks.find_one()
        if document:
            return True, document
        else:
            return False, "No task found in poolTasks."

    except PyMongoError as e:
        return False, f"An error occurred while accessing MongoDB: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred in find_pool_task: {e}"


def delete_inode_task(val_id):

    try:
        # Define the query based on val_id
        query = {"val_id": val_id}

        # Use find_one_and_delete to find and delete the document
        result = iNodeTask.find_one_and_delete(query)

        if result:
            return True, f"Task with val_id '{val_id}' deleted successfully."
        else:
            return False, f"No task found with val_id '{val_id}'."

    except PyMongoError as e:
        return False, f"An error occurred while accessing MongoDB: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred in delete_inode_task: {e}"


def delete_pool_task(val_id):
    try:
        # Define the query based on val_id
        query = {"val_id": val_id}

        # Use find_one_and_delete to find and delete the document
        result = poolTasks.find_one_and_delete(query)

        if result:
            return True, f"Task with val_id '{val_id}' deleted successfully."
        else:
            return False, f"No task found with val_id '{val_id}'."

    except PyMongoError as e:
        return False, f"An error occurred while accessing MongoDB: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred in delete_pool_task: {e}"
