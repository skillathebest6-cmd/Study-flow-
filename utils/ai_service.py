import os
import requests

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_student_context(student):
    """Construit le contexte de l'étudiant pour l'IA"""
    from models.user import Document, ServiceRequest, Payment
    from utils.document_requirements import get_required_documents, get_doc_label

    docs = Document.query.filter_by(student_id=student.id).all()
    submitted_types = [d.doc_type for d in docs]

    required = get_required_documents(student.nationality, student.destination_country, student.program_level)
    missing = [get_doc_label(d) for d in required if d not in submitted_types]

    requests_list = ServiceRequest.query.filter_by(student_id=student.id).all()
    pending_payments = Payment.query.filter_by(student_id=student.id, status='en_attente').all()

    context = f"""
Étudiant: {student.full_name}
Nationalité: {student.nationality or 'Non renseignée'}
Destination: {student.destination_country or 'Non renseignée'}
Programme: {student.program_level or 'Non renseigné'}
Statut du dossier: {student.status}
Documents soumis: {len(docs)}
Documents manquants: {', '.join(missing) if missing else 'Aucun'}
Demandes de service: {len(requests_list)} ({', '.join([r.service_type for r in requests_list]) if requests_list else 'aucune'})
Paiements en attente: {len(pending_payments)}
"""
    return context

def chat_with_ai(student, message):
    """Envoie un message à l'IA (Groq) avec le contexte de l'étudiant"""
    if not GROQ_API_KEY:
        return "Le support IA n'est pas encore configuré. Contactez l'administrateur."

    context = get_student_context(student)

    system_prompt = f"""Tu es l'assistant virtuel de StudyFlow, une plateforme d'accompagnement pour étudiants africains qui souhaitent étudier à l'étranger.

Contexte de l'étudiant actuel:
{context}

Règles:
- Réponds en français, de façon claire et concise (maximum 4-5 phrases)
- Sois chaleureux et encourageant
- Si l'étudiant demande des documents manquants, utilise le contexte ci-dessus
- Si tu ne sais pas répondre, invite l'étudiant à contacter l'équipe admin
- Ne donne jamais de conseils juridiques précis, seulement des informations générales
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"Désolé, une erreur est survenue. Veuillez réessayer plus tard."
