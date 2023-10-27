# vim:fenc=utf-8

# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import os
import sys
import uvicorn
import logging
from dotenv import dotenv_values
from .server_app import create_app, Settings

config = dotenv_values(".env")

settings = Settings(_env_file="model.env")
LOG_LEVEL = (
    logging.DEBUG if config.get("log_level", "info") == "debug" else logging.INFO
)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def run_serving():
    app = create_app(settings)
    host = config.get("host", "localhost")
    port = int(config.get("port", "9517"))
    logger.info(f"Starting serving at {host}:{port}")
    uvicorn.run(app, host=host, port=port)
