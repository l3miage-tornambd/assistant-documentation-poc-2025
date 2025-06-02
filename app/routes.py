from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import chatbot
import os
print("Current working directory:", os.getcwd())

bp = Blueprint('main', __name__)

# Liste pour stocker l'historique des conversations
conversation_history = []


@bp.route('/')
def index():
    """Page principale du chatbot"""
    # Initialiser le chatbot si nécessaire
    try:
        if not chatbot.is_initialized:
            chatbot.initialize()

        # Obtenir les statistiques
        num_documents = len(set(meta['filename'] for meta in chatbot.chunk_metadata)) if chatbot.chunk_metadata else 0
        num_chunks = len(chatbot.chunks)
        status_info = {
            'num_documents': num_documents,
            'num_chunks': num_chunks,
            'status': 'ready'
        }
    except Exception as e:
        status_info = {
            'num_documents': 0,
            'num_chunks': 0,
            'status': 'error',
            'error': str(e)
        }

    return render_template('index.html',
                           conversation=conversation_history,
                           status=status_info)


@bp.route('/chat', methods=['POST'])
def chat():
    """Traitement des questions du chatbot"""
    try:
        question = request.form.get('question', '').strip()

        if not question:
            flash('Veuillez saisir une question', 'error')
            return redirect(url_for('main.index'))

        # Ajouter la question à l'historique
        conversation_history.append({
            'type': 'user',
            'message': question
        })

        # Générer la réponse
        answer = chatbot.generate_answer(question)

        # Ajouter la réponse à l'historique
        conversation_history.append({
            'type': 'bot',
            'message': answer
        })

        # Limiter l'historique à 20 messages (10 échanges)
        if len(conversation_history) > 20:
            conversation_history[:] = conversation_history[-20:]

    except Exception as e:
        conversation_history.append({
            'type': 'bot',
            'message': f'Erreur lors du traitement: {str(e)}'
        })

    return redirect(url_for('main.index'))


@bp.route('/refresh', methods=['POST'])
def refresh_documents():
    """Rafraîchir l'index des documents"""
    try:
        chatbot.refresh_index()
        flash('Documents rafraîchis avec succès !', 'success')

        # Ajouter un message dans la conversation
        conversation_history.append({
            'type': 'system',
            'message': '✅ Documents rafraîchis avec succès !'
        })

    except Exception as e:
        flash(f'Erreur lors du rafraîchissement: {str(e)}', 'error')
        conversation_history.append({
            'type': 'system',
            'message': f'❌ Erreur lors du rafraîchissement: {str(e)}'
        })

    return redirect(url_for('main.index'))


@bp.route('/clear', methods=['POST'])
def clear_conversation():
    """Effacer l'historique de conversation"""
    conversation_history.clear()
    flash('Conversation effacée', 'info')
    return redirect(url_for('main.index'))