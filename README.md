# 🤖 Assistant Documentation - POC

Ce projet est un **Proof of Concept (POC)** d’assistant conversationnel pour interroger une documentation technique de manière interactive.  
Il utilise **Flask** pour le serveur web et un modèle de langage (via API ou local) pour répondre aux questions.

## 🚀 Versions requises

- **Python 3.11**

## ⚙️ Démarrage du projet

Voici les étapes à suivre pour démarrer le projet :

```bash
# 1️⃣ Crée un environnement virtuel avec Python 3.11
python -m venv venv

# 2️⃣ Active l'environnement virtuel
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3️⃣ Mets à jour pip et setuptools
python -m pip install --upgrade pip setuptools wheel

# 4️⃣ Installe les dépendances
python -m pip install -r requirements.txt

# 5️⃣ Lance le serveur Flask
python run.py