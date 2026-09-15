from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.history.history_manager import (
    buscar_conversas
)

from backend.core.engine.assistant import (
    AustinAssistant
)

from backend.core.ai.model_manager import (
    definir_modo,
    obter_status
)

from backend.core.system.server import (
    solicitar_shutdown
)


app = FastAPI(
    title="Austin API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


assistant = AustinAssistant()


class ChatRequest(BaseModel):

    message: str


class ChatResponse(BaseModel):

    response: str

    state: str

    requires_confirmation: bool = False

    session_ended: bool = False

    shutdown_requested: bool = False


class ModelModeRequest(BaseModel):

    mode: str


@app.get("/api/status")
def status():

    return assistant.status()


@app.get("/api/model/status")
def model_status():

    return obter_status()


@app.post("/api/model/mode")
def model_mode(
    request: ModelModeRequest
):

    definir_modo(
        request.mode
    )

    return {
        "status":
            obter_status()
    }


@app.post("/api/session")
def new_session():

    return assistant.new_session()


@app.post(
    "/api/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest
):

    return assistant.process_message(
        request.message
    )


@app.get("/api/history")
def history():

    return buscar_conversas()[-10:]


@app.post(
    "/api/history/open",
    response_model=ChatResponse
)
def open_history(
    request: dict
):

    arquivo = str(
        request.get(
            "arquivo",
            ""
        )
    ).strip()


    if not arquivo:

        return ChatResponse(
            response="Conversa inválida.",
            state="error"
        )


    return assistant.open_history(
        arquivo
    )


@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket
):

    await websocket.accept()


    try:

        while True:

            data = await websocket.receive_json()


            message = str(
                data.get(
                    "message",
                    ""
                )
            ).strip()


            if not message:

                await websocket.send_json({

                    "type":
                        "error",

                    "message":
                        "Mensagem vazia."

                })

                continue


            for evento in assistant.process_message_stream(
                message
            ):

                await websocket.send_json(
                    evento
                )


                if evento.get(
                    "shutdown_requested",
                    False
                ):

                    solicitar_shutdown()

                    return


    except WebSocketDisconnect:

        pass


    except Exception as erro:

        try:

            await websocket.send_json({

                "type":
                    "error",

                "message":
                    str(erro)

            })

        except Exception:

            pass


        try:

            await websocket.close()

        except Exception:

            pass


@app.get("/api/health")
def health():

    return {
        "status":
            "online"
    }