import logging
import os

import beeline


# https://docs.honeycomb.io/getting-data-in/python/beeline/#gunicorn
def post_worker_init(worker):
    logging.info(f"beeline initialization in process pid {os.getpid()}")
    beeline.init(
        writekey=os.environ.get("HONEYCOMB_API_KEY"),
        dataset=os.environ.get("ENVIRONMENT"),
        service_name="app",
    )
