import json
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from halatrans.config.config import Settings
from halatrans.model.services import AudioStreamControlRequest
from halatrans.services.frontend.audio_stream_service import (
    AudioStreamServiceParameters,
)
from halatrans.services.service_frontend_manager import FrontendServiceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GlobalInstance:
    def __init__(self):
        self.backend_service_manager: Optional[FrontendServiceManager] = None

    async def startup(self, settings: Settings):
        logger.info("Global instance startup.")
        self.frontend_service_manager = FrontendServiceManager()
        self.frontend_service_manager.start()
        logger.info("start frontend service manager.")

    def terminate(self):
        logger.info("Global instance terminate.")
        if self.frontend_service_manager:
            self.frontend_service_manager.terminate()
        self.frontend_service_manager = None

    def get_frontend_service_manager(self) -> Optional[FrontendServiceManager]:
        return self.frontend_service_manager


global_instance = GlobalInstance()


async def get_global_instance() -> GlobalInstance:
    global global_instance
    return global_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup env
    settings = Settings()

    # Logic to run at startup
    instance = await get_global_instance()
    await instance.startup(settings)
    try:
        yield
    finally:
        instance.terminate()


settings = Settings()
app = FastAPI(lifespan=lifespan)
if settings.mode == "dev":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
else:
    # TODO
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )


# Frontend API
@app.get("/api/devices")
async def devices_query(instance: GlobalInstance = Depends(get_global_instance)):
    audio_device = instance.get_frontend_service_manager().get_audio_device()

    input = bytes(
        json.dumps(
            {
                "cmd": "list-devices",
            }
        ),
        encoding="utf-8",
    )
    resp = await audio_device.request(input)
    return JSONResponse(json.loads(str(resp, encoding="utf-8")), status_code=200)


@app.post("/api/record")
async def start_record(
    req: AudioStreamControlRequest,
    instance: GlobalInstance = Depends(get_global_instance),
):
    # TODO: multi-user support

    if req.cmd == "start":
        p = AudioStreamServiceParameters()
        if req.deviceIndex >= 0:
            p.device = req.deviceIndex
        instance.get_frontend_service_manager().launch_audio_stream(p)
    elif req.cmd == "stop":
        instance.get_frontend_service_manager().stop_audio_stream()
    else:
        logger.error(f"Unknow command: {req}")

    return JSONResponse(dict(req), status_code=200)
