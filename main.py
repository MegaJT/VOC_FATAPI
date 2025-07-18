from fastapi import FastAPI, Request, HTTPException
import psycopg2
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI()

# PostgreSQL connection setup
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT", 5432)
)

@app.post("/webhook/typeform")
async def receive_typeform_webhook(request: Request):
    try:
        payload = await request.json()
        response_id = payload.get("event_id")
        submitted_at = payload.get("form_response", {}).get("submitted_at")
        answers = payload.get("form_response", {}).get("answers", [])
        
        # Insert into database
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO typeform_responses (response_id, submitted_at, answers, raw_payload)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (response_id) DO NOTHING;
            """, (
                response_id,
                submitted_at,
                json.dumps(answers),
                json.dumps(payload)
            ))
            conn.commit()

        return {"status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
