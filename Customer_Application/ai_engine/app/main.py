"""
main.py — FastAPI AI Engine entry point
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from app.db import get_customer_data
from app.analyser import analyse_customer
from app.groq_service import GroqService

load_dotenv()

app = FastAPI(title="NPN Banking AI Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_service = GroqService()


class AnalyseRequest(BaseModel):
    customer_id: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "NPN Banking AI Engine"}


@app.post("/analyse")
def analyse(request: AnalyseRequest):
    """
    Deep financial analysis for a customer.
    Returns health score, spending breakdown, gaps, NBO, and GenAI marketing message.
    """
    customer_id = request.customer_id.strip()

    data = get_customer_data(customer_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    analysis = analyse_customer(data)
    marketing_message = groq_service.generate_message(analysis)
    analysis["marketing_message"] = marketing_message

    return analysis
