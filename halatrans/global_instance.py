import logging

from halatrans.services.service_backend_manager import BackendServiceManager
from halatrans.services.service_frontend_manager import FrontendServiceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GlobalInstance:
    def __init__(self):
        self.backend_service_manager = BackendServiceManager()
        self.frontend_service_manager = FrontendServiceManager()

    def startup(self):
        logger.info("Global instance startup.")
        self.frontend_service_manager.start()

    def terminate(self):
        logger.info("Global instance terminate.")
        self.backend_service_manager.terminate()
        self.frontend_service_manager.terminate()

    def get_backend_service_manager(self) -> BackendServiceManager:
        return self.backend_service_manager

    def get_frontend_service_manager(self) -> FrontendServiceManager:
        return self.frontend_service_manager
