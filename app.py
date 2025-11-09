# app.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from chatbot_logic import process_message

load_dotenv()

app = FastAPI(title="Hospital Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    user_id: str = None
    text: str

@app.post("/message")
def message_endpoint(msg: Message):
    response = process_message(msg.user_id, msg.text)
    return response

@app.get("/")
def root():
    return {"status": "ok", "info": "Hospital Chatbot Backend"}
