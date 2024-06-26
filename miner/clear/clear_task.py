import os
import shutil
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s - %(message)s"
)


def delete_jobid_folder_and_file(job_folder, jobid, filename):
    try:
        jobid_path = os.path.join(os.getcwd(), job_folder, jobid)

        if not os.path.exists(jobid_path):
            raise FileNotFoundError(
                f"The folder '{jobid}' does not exist in '{job_folder}'."
            )

        file_path = os.path.join(jobid_path, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            # print(f"Deleted file: {filename}")
        else:
            print(f"The file '{filename}' does not exist in '{jobid}'.")

        if not os.listdir(jobid_path):
            shutil.rmtree(jobid_path)
            # print(f"Deleted empty folder: {jobid}")
        else:
            print(f"Folder '{jobid}' is not empty, so it was not deleted.")

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")


def clear_directory(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.error("Failed to delete %s. Reason: %s", file_path, e)
