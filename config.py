import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Chemins des dossiers
    DOCUMENTS_FOLDER = 'data/documents'
    VECTORSTORE_FOLDER = 'vectorstore'

    # Configuration du modèle
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'  # Modèle léger et efficace
    GENERATION_MODEL = 'microsoft/DialoGPT-medium'  # Ou utilisez un modèle français si préféré

    # Paramètres de recherche
    SIMILARITY_THRESHOLD = 0.5  # Seuil de similarité minimum
    MAX_CHUNKS_FOR_ANSWER = 3  # Nombre maximum de chunks à utiliser pour la réponse
    CHUNK_SIZE = 500  # Taille des chunks en caractères
    CHUNK_OVERLAP = 50  # Chevauchement entre chunks