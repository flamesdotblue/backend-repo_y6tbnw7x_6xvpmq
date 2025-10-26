import os
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from database import db, create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestOtpPayload(BaseModel):
    email: EmailStr


class VerifyOtpPayload(BaseModel):
    email: EmailStr
    code: str


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os

    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# OTP Auth Endpoints
@app.post("/auth/request-otp")
def request_otp(payload: RequestOtpPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    email = payload.email.lower().strip()
    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Store OTP record
    otp_doc = {
        "email": email,
        "code": code,
        "expires_at": expires_at,
        "used": False,
    }
    create_document("otp", otp_doc)

    # Optionally ensure user exists (create lightweight record)
    existing = db["authuser"].find_one({"email": email})
    if not existing:
        db["authuser"].insert_one({
            "email": email,
            "display_name": None,
            "is_verified": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

    # In a production app you'd send the OTP via email provider.
    # For this demo we return it so you can log in.
    return {
        "message": "OTP sent to your email",
        "dev_otp": code,
        "expires_in_seconds": 300,
    }


@app.post("/auth/verify-otp")
def verify_otp(payload: VerifyOtpPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    email = payload.email.lower().strip()
    code = payload.code.strip()

    now = datetime.now(timezone.utc)

    otp = db["otp"].find_one(
        {
            "email": email,
            "code": code,
            "used": False,
            "expires_at": {"$gte": now},
        },
        sort=[("created_at", -1)],
    )

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    # Mark OTP as used
    db["otp"].update_one({"_id": otp["_id"]}, {"$set": {"used": True, "updated_at": now}})

    # Mark user as verified and update last_login
    db["authuser"].update_one(
        {"email": email},
        {"$set": {"is_verified": True, "last_login": now, "updated_at": now}},
        upsert=True,
    )

    # Issue a simple demo token (not a real JWT)
    token = f"demo-token-{email}"

    return {"success": True, "token": token, "email": email}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
