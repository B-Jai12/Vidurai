# Language settings
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Bengali": "bn",
    "Kannada": "kn",
    "Marathi": "mr"
}

# Medicine frequency to times per day
FREQUENCY_MAP = {
    "OD": 1,   # Once daily
    "BD": 2,   # Twice daily
    "TDS": 3,  # Three times daily
    "QID": 4,  # Four times daily
    "HS": 1,   # Bedtime
    "SOS": 0,  # As needed
    "AC": 3,   # Before food
    "PC": 3,   # After food
}

# Frequency to human readable
FREQUENCY_LABELS = {
    "OD": "Once Daily",
    "BD": "Twice Daily",
    "TDS": "Three Times Daily",
    "QID": "Four Times Daily",
    "HS": "At Bedtime",
    "SOS": "As Needed",
    "AC": "Before Food",
    "PC": "After Food",
}

# Controlled substances list
CONTROLLED_SUBSTANCES = [
    "tramadol", "codeine", "alprazolam", "diazepam",
    "clonazepam", "lorazepam", "morphine", "oxycodone",
    "fentanyl", "buprenorphine", "zolpidem", "nitrazepam"
]

# Condition to specialist mapping
SPECIALTY_MAP = {
    "diabetes": "endocrinologist",
    "hypertension": "cardiologist",
    "heart": "cardiologist",
    "thyroid": "endocrinologist",
    "asthma": "pulmonologist",
    "depression": "psychiatrist",
    "anxiety": "psychiatrist",
    "fracture": "orthopedic",
    "infection": "general physician",
    "fever": "general physician",
    "kidney": "nephrologist",
    "liver": "hepatologist",
    "eye": "ophthalmologist",
    "skin": "dermatologist",
    "bone": "orthopedic",
}

# App colors
COLORS = {
    "primary": "#1A73E8",
    "success": "#34A853",
    "warning": "#FBBC04",
    "danger":  "#EA4335",
    "light":   "#F8F9FA",
    "dark":    "#202124",
}

# Disclaimer
DISCLAIMER = "MedSaathi is not a substitute for professional medical advice. Always consult your doctor."