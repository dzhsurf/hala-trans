import logging
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, Generator, Optional

from halatrans.services.base_service import (CustomService,
                                             PublishSubscribeService,
                                             RequestResponseService,
                                             ServiceConfig)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceTemplateA(RequestResponseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_response(
        parameters: Dict[str, Any], topic: str, chunk: bytes
    ) -> Optional[bytes]:
        # override this method
        pass


class ServiceTemplateB(PublishSubscribeService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_publisher(
        parameters: Dict[str, Any],
    ) -> Generator[bytes, Optional[str], None]:
        # override this method
        pass


class ServiceTemplateC(CustomService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def on_worker_process_custom(
        stop_flag: ValueProxy[int], parameters: Dict[str, Any]
    ):
        # override this method
        pass
