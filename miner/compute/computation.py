import os
import logging
import json
import asyncio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


async def compute_task(task_id, task_description, task_seed):
    try:
        task_description
        task_seed
        # Simple task processing logic..
        result = {
            "id": task_id,
            "output": "sample_output",
        }
        print("Simulating computing")
        await asyncio.sleep(20)
        print("After computing")
        output = json.dumps(result)

        # store completed task or do something..
        logging.info("Task Completed successfully.")
        return True, output
    except Exception as e:
        logging.error(f"Error processing task: {e}")
        return False, None
