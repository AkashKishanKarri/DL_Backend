---
title: Face Attendance Backend
emoji: rocket
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# Face Attendance Backend (Hugging Face Space)

This backend is a FastAPI service that performs member enrollment and face recognition attendance using `facenet-pytorch`.

## Environment variables

Set this secret in your Hugging Face Space settings:

- `FIREBASE_CREDENTIALS`: Full Firebase service account JSON (single-line JSON string)

## Local run

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 7860
```

## Deploy notes

- This Space uses Docker (`sdk: docker`).
- Port `7860` is exposed and used by the container.
- `serviceAccountKey.json` is ignored; use `FIREBASE_CREDENTIALS` instead.
