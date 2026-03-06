from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import shutil
import os

from face_recog import get_average_embedding, recognize_faces
from firebase_config import db

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# API Home Route removed to serve frontend at root


# ------------------------------
# Enroll Member
# ------------------------------
@app.post("/enroll/")
async def enroll_member(
    name: str = Form(...),
    email: str = Form(...),
    domain: str = Form(...),
    files: List[UploadFile] = File(...)
):

    image_paths = []

    for file in files:
        file_path = f"{UPLOAD_FOLDER}/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_paths.append(file_path)

    avg_embedding = get_average_embedding(image_paths)

    if avg_embedding is None:
        return {"error": "No face detected"}

    db.collection("members").add({
    "name": name,
    "email": email,
    "domain": domain,
    "embedding": avg_embedding
    })

    return {"message": f"{name} enrolled successfully"}


# ------------------------------
# Recognize Faces
# ------------------------------
@app.post("/recognize/")
async def recognize_attendance(file: UploadFile = File(...)):

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    members = db.collection("members").stream()

    known_embeddings = {}
    all_emails = []

    for member in members:
        data = member.to_dict()
        known_embeddings[data["email"]] = list(data["embedding"])
        all_emails.append(data["email"])

    recognized = recognize_faces(file_path, known_embeddings)

    absent = list(set(all_emails) - set(recognized))

    return {
        "present": recognized,
        "absent": absent
    }


@app.get("/attendance/")
def get_attendance():

    records = db.collection("attendance").stream()

    result = []

    for r in records:

        data = r.to_dict()

        result.append({
            "event_name": data["event_name"],
            "present": data["present"]
        })

    return result

# ------------------------------
# Save Attendance
# ------------------------------
@app.post("/attendance/save")
async def save_attendance(data: dict):

    record = {
        "event_name": data["event_name"],
        "domain": data["domain"],
        "event_date": datetime.now().strftime("%Y-%m-%d"),
        "present": data["present"],
        "timestamp": datetime.now()
    }

    db.collection("attendance").add(record)

    return {"message": "Attendance saved"}


@app.get("/members/{domain}")
def get_members(domain: str):

    members = []

    docs = db.collection("users").stream()

    for doc in docs:
        data = doc.to_dict()

        if data.get("domain", "").lower() == domain.lower():
            members.append({
                "name": data.get("name"),
                "email": data.get("email")
            })

    return members

# ------------------------------
# Serve React Frontend
# ------------------------------
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))
assets_dir = os.path.join(dist_dir, "assets")

if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if not os.path.isdir(dist_dir):
        return {"error": "Frontend build not found. Run 'npm run build' in frontend directory."}
        
    if full_path:
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
    index_file = os.path.join(dist_dir, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
        
    return {"error": "index.html not found"}
