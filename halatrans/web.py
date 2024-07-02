import asyncio
import json
import logging
import queue
import time
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from halatrans.global_instance import GlobalInstance
from halatrans.model.services import AudioStreamControlRequest, ServiceRequest
from halatrans.services.backend.rts2t_service import RTS2TService
from halatrans.services.frontend.audio_stream_service import \
    AudioStreamServiceParameters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


global_instance = GlobalInstance()


async def get_global_instance() -> GlobalInstance:
    global global_instance
    return global_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    instance = await get_global_instance()
    instance.startup()
    try:
        yield
    finally:
        await get_global_instance().terminate()


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
    state = "Running" if instance.get_backend_service_manager().is_running else ""
    content = {
        "runningState": state,
    }
    return JSONResponse(content, status_code=200)


@app.post("/api/service_management")
async def service_management_ctrl(
    request: ServiceRequest,
    instance: GlobalInstance = Depends(get_global_instance),
):
    msg = instance.get_backend_service_manager().run_command(request.cmd)
    content = {"message": msg}
    return JSONResponse(content, status_code=200)


@app.get("/api/event_stream")
async def event_stream(instance: GlobalInstance = Depends(get_global_instance)):
    async def poll_queue():
        while True:
            if not instance.get_backend_service_manager().is_running:
                break
            item = None
            service: RTS2TService = instance.get_backend_service_manager().get_service(
                "rts2t-main"
            )
            if service is None:
                # service not started
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
            wait_time = 0.5 if item is None else 0.1
            yield f"data: {json.dumps(msg)}\n\n"
            await asyncio.sleep(wait_time)

    return StreamingResponse(poll_queue(), media_type="text/event-stream")


# Frontend API
@app.get("/api/devices")
async def devices_query(instance: GlobalInstance = Depends(get_global_instance)):
    audio_device = instance.get_frontend_service_manager().get_audio_device()

    input = json.dumps(
        {
            "cmd": "list-device",
        }
    )
    resp = await audio_device.request(input)
    return JSONResponse(json.loads(resp), status_code=200)


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
