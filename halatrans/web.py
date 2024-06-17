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
from halatrans.model.services import ServiceRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


global_instance = GlobalInstance()


async def get_global_instance() -> GlobalInstance:
    global global_instance
    return global_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    # instance = await get_global_instance()
    # instance.startup()
    try:
        yield
    finally:
        print("")
        # await get_global_instance().terminate()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/internal/services")
async def api_services():
    content = {}
    return JSONResponse(content, status_code=200)


@app.post("/internal/services")
async def api_launch_services(
    request: ServiceRequest,
    background_tasks: BackgroundTasks,
    instance: GlobalInstance = Depends(get_global_instance),
):
    msg = instance.get_service_manager().run_command(request.cmd)
    content = {"message": msg}
    return JSONResponse(content, status_code=200)


@app.get("/api/streaming")
async def api_streaming(instance: GlobalInstance = Depends(get_global_instance)):
    async def poll_queue():
        q = instance.get_service_manager().get_service_msg_queue("rts2t")
        while True:
            if instance.get_service_manager().is_terminating:
                break
            item = None
            if q is None:
                q = instance.get_service_manager().get_service_msg_queue("rts2t")
            else:
                try:
                    chunk = q.get(block=False)
                    item = json.loads(chunk)
                except queue.Empty:
                    pass
            msg = {"item": item}
            yield f"data: {json.dumps(msg)}\n\n"
            await asyncio.sleep(0.2)

    return StreamingResponse(poll_queue(), media_type="text/event-stream")
