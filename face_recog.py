import face_recognition
import numpy as np

import os
os.environ["OMP_NUM_THREADS"] = "1"


def get_average_embedding(image_paths):

    embeddings = []

    for path in image_paths:
        image = face_recognition.load_image_file(path)

        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            embeddings.append(encodings[0])  # 128-dim vector

    if len(embeddings) == 0:
        return None

    avg_embedding = np.mean(embeddings, axis=0)

    return avg_embedding.tolist()


def recognize_faces(image_path, known_embeddings):

    image = face_recognition.load_image_file(image_path)

    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    recognized = []

    for face_encoding in face_encodings:

        for email, embedding in known_embeddings.items():

            embedding = np.array(embedding)

            # Skip invalid embeddings (like 512-dim ones)
            if embedding.shape[0] != 128:
                continue

            distance = face_recognition.face_distance(
                [embedding],
                face_encoding
            )[0]

            if distance < 0.45:
                recognized.append(email)

    return recognized
