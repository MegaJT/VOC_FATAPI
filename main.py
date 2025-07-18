from fastapi import FastAPI, Request, HTTPException
import psycopg2
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

app = FastAPI()

# Configure basic logging
logging.basicConfig(level=logging.INFO)


@app.post("/webhook/typeform")
async def receive_typeform_webhook(request: Request):
    try:
        # Parse incoming request body
        body_bytes = await request.body()
        payload = json.loads(body_bytes)

        response_id = payload.get("event_id")
        submitted_at = payload.get("form_response", {}).get("submitted_at")
        answers = payload.get("form_response", {}).get("answers", [])

        # [3] Validate required fields
        if not response_id or not submitted_at:
            logging.warning("Missing response_id or submitted_at in payload")
            raise HTTPException(status_code=400, detail="Missing required fields")

        # [5] Log basic info
        logging.info(f"Received Typeform response: {response_id} at {submitted_at}")

        # Connect to PostgreSQL and insert
        with psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", 5432)
        ) as conn:
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
        logging.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
