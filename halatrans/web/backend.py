import asyncio
import json
import logging
import queue
import time
from contextlib import asynccontextmanager
from typing import Any, Optional, Tuple, Type

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from halatrans.config.config import Settings
from halatrans.model.services import ServiceRequest
from halatrans.services.backend.rts2t_service import RTS2TService
from halatrans.services.service_backend_manager import BackendServiceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GlobalInstance:
    def __init__(self):
        self.backend_service_manager: Optional[BackendServiceManager] = None

    async def startup(self, settings: Settings):
        logger.info("Global instance startup.")
        self.backend_service_manager = BackendServiceManager()
        self.backend_service_manager.start()
        logger.info("start backend service manager.")

    def terminate(self):
        logger.info("Global instance terminate.")
        if self.backend_service_manager:
            self.backend_service_manager.terminate()
        self.backend_service_manager = None

    def get_backend_service_manager(self) -> Optional[BackendServiceManager]:
        return self.backend_service_manager


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


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Backend API
@app.get("/api/service_management")
async def service_management_query(
    instance: GlobalInstance = Depends(get_global_instance),
):
    mgr = instance.get_backend_service_manager()
    if mgr:
        state = "Running" if mgr.is_running else ""
        content = {
            "runningState": state,
        }
    else:
        content = {
            "runningState": "",
        }
    return JSONResponse(content, status_code=200)


@app.post("/api/service_management")
async def service_management_ctrl(
    request: ServiceRequest,
    instance: GlobalInstance = Depends(get_global_instance),
):
    mgr = instance.get_backend_service_manager()
    if mgr:
        msg = mgr.run_command(request.cmd)
    else:
        msg = {"message": "Service not started."}
    content = {"message": msg}
    return JSONResponse(content, status_code=200)


@app.get("/api/event_stream")
async def event_stream(instance: GlobalInstance = Depends(get_global_instance)):
    async def poll_queue():
        while True:
            mgr = instance.get_backend_service_manager()
            if (mgr is None) or (not mgr.is_running):
                break
            item = None
            service: RTS2TService = mgr.get_service("rts2t-main")
            if service is None:
                # service not started
                # logger.info("service is empty.")
                yield f"data: {json.dumps({'item': None})}\n\n"
                await asyncio.sleep(1)
                continue
            else:
                # service is runnning
                try:
                    result_queue = service.get_output_msg_queue()
                    chunk = result_queue.get(block=False)
                    item = json.loads(chunk)
                except queue.Empty:
                    pass
            if item and "msg_type" in item:
                msg_type = item["msg_type"]
                if msg_type == "assistant":
                    msg = {"assistant": item["assistant"]}
                else:
                    msg = {"item": item}
            else:
                msg = {"item": item}
            # wait more time if no msg recv
            # logger.info(f"item: {item}")
            wait_time = 0.5 if item is None else 0.1
            yield f"data: {json.dumps(msg)}\n\n"
            await asyncio.sleep(wait_time)

    return StreamingResponse(poll_queue(), media_type="text/event-stream")
