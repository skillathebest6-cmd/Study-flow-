DOCUMENT_REQUIREMENTS = {
    'Guinée': {
        'France': {
            'Licence': ['passeport', 'releves_notes', 'lettre_motivation', 'cv'],
            'Master': ['passeport', 'releves_notes', 'lettre_motivation', 'cv', 'lettre_recommandation'],
        },
        'Canada': {
            'Licence': ['passeport', 'releves_notes', 'cv'],
            'Master': ['passeport', 'releves_notes', 'cv', 'lettre_recommandation'],
        },
        'Belgique': {
            'Licence': ['passeport', 'releves_notes', 'acte_naissance'],
            'Master': ['passeport', 'releves_notes', 'cv', 'acte_naissance'],
        },
    },
    'Mali': {
        'France': {
            'Licence': ['passeport', 'releves_notes', 'cv'],
            'Master': ['passeport', 'releves_notes', 'cv', 'lettre_recommandation'],
        },
        'Canada': {
            'Licence': ['passeport', 'releves_notes'],
        },
    },
    'Sénégal': {
        'France': {
            'Licence': ['passeport', 'releves_notes', 'cv'],
        },
        'Canada': {
            'Licence': ['passeport', 'releves_notes', 'cv'],
        },
        'Belgique': {
            'Licence': ['passeport', 'releves_notes', 'acte_naissance'],
        },
    },
    'Liberia': {
        'USA': {
            'Licence': ['passeport', 'releves_notes', 'lettre_motivation'],
            'Master': ['passeport', 'releves_notes', 'cv', 'lettre_recommandation'],
        },
        'UK': {
            'Licence': ['passeport', 'lettre_motivation'],
        },
    },
}

DOC_LABELS = {
    'passeport': 'Passeport',
    'releves_notes': 'Relevés de notes',
    'diplome': 'Diplôme',
    'cv': 'CV',
    'lettre_motivation': 'Lettre de motivation',
    'lettre_recommandation': 'Lettre de recommandation',
    'acte_naissance': 'Acte de naissance',
    'photo_identite': "Photo d'identité",
    'justificatif': 'Justificatif de domicile',
    'certificat_medical': 'Certificat médical',
}

def get_required_documents(nationality, destination, program_level):
    """Récupère la liste des documents requis (codes) selon le profil de l'étudiant"""
    country_reqs = DOCUMENT_REQUIREMENTS.get(nationality, {})
    dest_reqs = country_reqs.get(destination, {})
    required = dest_reqs.get(program_level, [])

    if not required:
        required = ['passeport', 'releves_notes', 'cv', 'lettre_motivation']

    return required

def get_doc_label(doc_code):
    """Convertit un code (ex: 'releves_notes') en libellé lisible (ex: 'Relevés de notes')"""
    return DOC_LABELS.get(doc_code, doc_code.replace('_', ' ').capitalize())
