import os
from datetime import datetime

from loguru import logger

from .pipeline import run_pipeline


def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join("outputs", "logs")
    os.makedirs(out_dir, exist_ok=True)
    logger.add(os.path.join(out_dir, f"run_{run_id}.log"))

    logger.info(f"Starting doctr_process run_id={run_id}")
    # TODO: load .env / configs as needed
    # from dotenv import load_dotenv; load_dotenv()

    # This is your entrypoint; adapt args as needed
    run_pipeline(run_id=run_id)
    logger.info("Finished")

