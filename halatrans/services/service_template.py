import logging
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq

from halatrans.services.base_service import BaseService, ServiceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceTemplate(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
