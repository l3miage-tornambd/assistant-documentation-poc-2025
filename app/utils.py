import os
import re
from typing import List, Tuple


def read_documents(documents_folder: str) -> List[Tuple[str, str]]:
    """
    Lit tous les documents du dossier et retourne une liste de tuples (nom_fichier, contenu)
    """
    documents = []

    if not os.path.exists(documents_folder):
        os.makedirs(documents_folder)
        return documents

    for filename in os.listdir(documents_folder):
        if filename.endswith(('.txt', '.md', '.doc')):
            filepath = os.path.join(documents_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    documents.append((filename, content))
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier {filename}: {e}")

    return documents


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Découpe un texte en chunks avec chevauchement
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Si on n'est pas à la fin du texte, essayer de couper à un espace
        if end < len(text):
            # Chercher le dernier espace avant la limite
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Préparer le prochain chunk avec chevauchement
        start = end - overlap
        if start >= len(text):
            break

    return chunks


def clean_text(text: str) -> str:
    """
    Nettoie le texte en supprimant les caractères indésirables
    """
    # Supprimer les caractères de contrôle
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)

    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()