import logging

from .services.manager import ServiceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GlobalInstance:
    def __init__(self):
        self.state = {}
        self.service_manager = ServiceManager()

    def startup(self):
        logger.info("Global instance startup.")

    def terminate(self):
        logger.info("Global instance terminate.")
        self.service_manager.terminate()

    def get_state(self):
        return self.state

    def get_service_manager(self) -> ServiceManager:
        return self.service_manager
