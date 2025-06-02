import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional
from flask import current_app
from app.utils import read_documents, split_text_into_chunks, clean_text


class DocumentChatbot:
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.chunks = []
        self.chunk_metadata = []  # Pour stocker les métadonnées des chunks
        self.is_initialized = False

    def initialize(self):
        """Initialise le modèle d'embedding et charge/crée l'index"""
        if self.is_initialized:
            return

        print("Initialisation du modèle d'embedding...")
        self.embedding_model = SentenceTransformer(current_app.config['EMBEDDING_MODEL'])

        # Tenter de charger un index existant
        if not self._load_index():
            print("Aucun index trouvé, création d'un nouvel index...")
            self._create_index()

        self.is_initialized = True
        print(f"Chatbot initialisé avec {len(self.chunks)} chunks")

    def _load_index(self) -> bool:
        """Charge l'index et les chunks depuis les fichiers sauvegardés"""
        vectorstore_path = current_app.config['VECTORSTORE_FOLDER']
        index_path = os.path.join(vectorstore_path, 'faiss_index')
        chunks_path = os.path.join(vectorstore_path, 'chunks.pkl')
        metadata_path = os.path.join(vectorstore_path, 'metadata.pkl')

        if not all(os.path.exists(path) for path in [index_path, chunks_path, metadata_path]):
            return False

        try:
            # Charger l'index FAISS
            self.index = faiss.read_index(index_path)

            # Charger les chunks et métadonnées
            with open(chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)

            with open(metadata_path, 'rb') as f:
                self.chunk_metadata = pickle.load(f)

            return True
        except Exception as e:
            print(f"Erreur lors du chargement de l'index: {e}")
            return False

    def _save_index(self):
        """Sauvegarde l'index et les chunks"""
        vectorstore_path = current_app.config['VECTORSTORE_FOLDER']
        os.makedirs(vectorstore_path, exist_ok=True)

        # Sauvegarder l'index FAISS
        index_path = os.path.join(vectorstore_path, 'faiss_index')
        faiss.write_index(self.index, index_path)

        # Sauvegarder les chunks
        chunks_path = os.path.join(vectorstore_path, 'chunks.pkl')
        with open(chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)

        # Sauvegarder les métadonnées
        metadata_path = os.path.join(vectorstore_path, 'metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.chunk_metadata, f)

    def _create_index(self):
        """Crée un nouvel index à partir des documents"""
        documents = read_documents(current_app.config['DOCUMENTS_FOLDER'])

        if not documents:
            print("Aucun document trouvé dans le dossier des documents")
            # Créer un index vide
            self.index = faiss.IndexFlatIP(384)  # Dimension du modèle all-MiniLM-L6-v2
            self.chunks = []
            self.chunk_metadata = []
            return

        all_chunks = []
        all_metadata = []

        # Traiter chaque document
        for filename, content in documents:
            print(f"Traitement du document: {filename}")
            cleaned_content = clean_text(content)

            # Découper en chunks
            chunks = split_text_into_chunks(
                cleaned_content,
                current_app.config['CHUNK_SIZE'],
                current_app.config['CHUNK_OVERLAP']
            )

            # Ajouter les chunks et leurs métadonnées
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadata.append({
                    'filename': filename,
                    'chunk_id': i,
                    'text': chunk
                })

        if not all_chunks:
            print("Aucun chunk créé à partir des documents")
            self.index = faiss.IndexFlatIP(384)
            self.chunks = []
            self.chunk_metadata = []
            return

        # Créer les embeddings
        print("Création des embeddings...")
        embeddings = self.embedding_model.encode(all_chunks)
        embeddings = embeddings.astype('float32')

        # Normaliser pour utiliser le produit scalaire comme mesure de similarité cosinus
        faiss.normalize_L2(embeddings)

        # Créer l'index FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product pour similarité cosinus
        self.index.add(embeddings)

        self.chunks = all_chunks
        self.chunk_metadata = all_metadata

        # Sauvegarder
        self._save_index()
        print(f"Index créé avec {len(all_chunks)} chunks")

    def search_similar_chunks(self, query: str, k: int = 5) -> List[Tuple[str, float, dict]]:
        """Recherche les chunks les plus similaires à la requête"""
        if not self.is_initialized:
            self.initialize()

        if len(self.chunks) == 0:
            return []

        # Créer l'embedding de la requête
        query_embedding = self.embedding_model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Rechercher
        scores, indices = self.index.search(query_embedding, min(k, len(self.chunks)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks) and score >= current_app.config['SIMILARITY_THRESHOLD']:
                results.append((
                    self.chunks[idx],
                    float(score),
                    self.chunk_metadata[idx]
                ))

        return results

    def generate_answer(self, query: str) -> str:
        """Génère une réponse basée sur les documents"""
        if not self.is_initialized:
            self.initialize()

        # Rechercher les chunks pertinents
        similar_chunks = self.search_similar_chunks(
            query,
            current_app.config['MAX_CHUNKS_FOR_ANSWER']
        )

        if not similar_chunks:
            return "Je ne sais pas"

        # Construire le contexte à partir des chunks les plus pertinents
        context_parts = []
        for chunk, score, metadata in similar_chunks:
            context_parts.append(f"Document {metadata['filename']}: {chunk}")

        context = "\n\n".join(context_parts)

        # Créer une réponse simple basée sur le contexte
        # Pour un POC, on peut utiliser une approche basique
        # Dans une version plus avancée, vous pourriez utiliser un modèle de génération

        response = self._create_simple_response(query, context, similar_chunks)
        return response

    def _create_simple_response(self, query: str, context: str, chunks: List[Tuple[str, float, dict]]) -> str:
        """Crée une réponse simple basée sur le contexte"""
        # Pour ce POC, on retourne le chunk le plus pertinent avec quelques améliorations
        if not chunks:
            return "Je ne sais pas"

        best_chunk, best_score, best_metadata = chunks[0]

        # Si la similarité est très faible, on refuse de répondre
        if best_score < current_app.config['SIMILARITY_THRESHOLD']:
            return "Je ne sais pas"

        # Formater la réponse
        response = f"Basé sur le document '{best_metadata['filename']}':\n\n{best_chunk}"

        # Si on a plusieurs chunks pertinents, les mentionner
        if len(chunks) > 1:
            other_sources = set(chunk[2]['filename'] for chunk in chunks[1:])
            if other_sources:
                response += f"\n\n(Informations complémentaires trouvées dans: {', '.join(other_sources)})"

        return response

    def refresh_index(self):
        """Recrée l'index à partir des documents actuels"""
        print("Rafraîchissement de l'index...")
        self._create_index()
        print("Index rafraîchi")


# Instance globale du chatbot
chatbot = DocumentChatbot()