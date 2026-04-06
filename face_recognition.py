import torch
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

mtcnn = MTCNN(keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)


def get_embedding_from_image(image_path):
    img = Image.open(image_path)
    faces = mtcnn(img)

    if faces is None:
        return None

    embeddings = resnet(faces.to(device))
    return embeddings[0].detach().cpu().numpy()


def get_average_embedding(image_paths):
    embedding_list = []

    for path in image_paths:
        emb = get_embedding_from_image(path)
        if emb is not None:
            embedding_list.append(emb)

    if len(embedding_list) == 0:
        return None

    avg_embedding = np.mean(embedding_list, axis=0)
    return avg_embedding

def cosine_similarity(emb1, emb2):
    emb1 = emb1 / np.linalg.norm(emb1)
    emb2 = emb2 / np.linalg.norm(emb2)
    return np.dot(emb1, emb2)

def recognize_faces(image_path, known_embeddings, threshold=0.75): #higher the threshold higher the strictness during recognition
    
    from PIL import Image
    
    img = Image.open(image_path)
    faces = mtcnn(img)

    if faces is None:
        return []

    detected_embeddings = resnet(faces.to(device))
    detected_embeddings = detected_embeddings.detach().cpu().numpy()

    recognized_names = []

    for emb in detected_embeddings:
        best_match = None
        best_similarity = -1
        
        for name, known_emb in known_embeddings.items():
            similarity = cosine_similarity(emb, np.array(known_emb))
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = name
                
        if best_match is not None and best_similarity > threshold:
            recognized_names.append(best_match)

    return recognized_names