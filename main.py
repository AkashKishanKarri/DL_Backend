from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil
import os
from datetime import datetime

from face_recognition import get_average_embedding, recognize_faces
from firebase_config import db

app = FastAPI()

# CORS to allow different domains to access the site
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "temp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Backend Running"}


@app.get("/enroll-camera", response_class=HTMLResponse)
def enroll_camera_page(request: Request):

    uid = request.query_params.get("uid")
    email = request.query_params.get("email")
    name = request.query_params.get("name")

    return templates.TemplateResponse(
        "enroll_camera.html",
        {
            "request": request,
            "uid": uid,
            "email": email,
            "name": name
        }
    )


@app.post("/enroll/")
async def enroll_member(
    uid: str,
    email: str,
    files: List[UploadFile] = File(...)
):
    image_paths = []

    for file in files:
        file_path = f"{UPLOAD_FOLDER}/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_paths.append(file_path)

    avg_embedding = get_average_embedding(image_paths)

    for path in image_paths:
        if os.path.exists(path):
            os.remove(path)

    if avg_embedding is None:
        return {"error": "No valid faces detected"}

    db.collection("members").document(uid).set({
    "embedding": avg_embedding.tolist()
}, merge=True)

    return {"message": f"User enrolled successfully"}


@app.post("/recognize/")
async def recognize_attendance(file: UploadFile = File(...)):

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Fetch members
    members = db.collection("members").stream() #Read

    known_embeddings = {}
    all_member_emails = []

    for member in members:
        data = member.to_dict()
        email = data.get("email", "Unknown")
        if "embedding" in data:
            known_embeddings[email] = data["embedding"]
        all_member_emails.append(email)

    recognized = list(set(recognize_faces(file_path, known_embeddings)))

    if os.path.exists(file_path):
        os.remove(file_path)

    absent = list(set(all_member_emails) - set(recognized))

    attendance_record = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "present": recognized,
        "absent": absent,
        "total_present": len(recognized)
    } #Create

    return attendance_record


@app.get("/members")
def get_members():
    members = db.collection("members").stream()
    names = []

    for member in members:
        data = member.to_dict()
        names.append({
    "email": data.get("email"),
    "name": data.get("name", data.get("email", "Unknown")),
    "domain": data.get("domain", "Unknown"),
    "year_of_study": data.get("year_of_study", "Unknown"),
    "role": data.get("role", "member")
}) #Read

    return names


@app.get("/attendance/")
def get_attendance():

    records = db.collection("attendance").stream()
    data = []

    for record in records:
        rec_dict = record.to_dict()
        rec_dict["id"] = record.id
        data.append(rec_dict)

    return data


@app.put("/attendance/update/{record_id}") #Update
async def update_attendance(record_id: str, data: dict):
    members = db.collection("members").stream()
    all_members = [m.to_dict().get("email", "Unknown") for m in members]

    present = data["present"]
    absent = list(set(all_members) - set(present))

    db.collection("attendance").document(record_id).update({
        "event_name": data["event_name"],
        "present": present,
        "absent": absent
    })

    return {"message": "Attendance updated"}

@app.delete("/attendance/delete/{record_id}") #Delete
async def delete_attendance(record_id: str):
    db.collection("attendance").document(record_id).delete()
    return {"message": "Attendance deleted"}

@app.post("/attendance/save") #Save
async def save_attendance(data: dict):

    members = db.collection("members").stream()
    all_members = [m.to_dict().get("email", "Unknown") for m in members]

    present = data["present"]
    absent = list(set(all_members) - set(present))

    record = {
        "event_name": data["event_name"],
        "event_date": datetime.now().strftime("%Y-%m-%d"),
        "present": present,
        "absent": absent,
        "timestamp": datetime.now()
    }

    db.collection("attendance").add(record)

    return {"message": "Attendance saved"}