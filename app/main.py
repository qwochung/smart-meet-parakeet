from app.models.asr_parakeet import load_model
from starlette.middleware.cors import CORSMiddleware

from fastapi import FastAPI
from app.api import transcribe

app = FastAPI(
    title="SmartMeet AI API",
    version="1.0.0"
)

# Cấu hình chống lỗi CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong thực tế có thể đổi thành "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcribe.router)

@app.on_event("startup")
async def startup_event():
    print("Loading nemo_models...")
    load_model()

@app.get("/")
def root():
    return {"message": "Server is running"}
