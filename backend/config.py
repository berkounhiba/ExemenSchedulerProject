
import os

# ============================================
# DATABASE CONFIGURATION
# ============================================
try:
    
    import streamlit as st
    # Running on Streamlit Cloud - use secrets
    DB_CONFIG = {
        'dbname': st.secrets["database"]["database"],
        'user': st.secrets["database"]["user"],
        'password': st.secrets["database"]["password"],
        'host': st.secrets["database"]["host"],
        'port': st.secrets["database"].get("port", 5432)
    }
except (ImportError, FileNotFoundError, KeyError):
   DB_CONFIG = {
    'dbname': 'neondb',
    'user': 'neondb_owner',
    'host': 'ep-little-frost-ahn9lgxm-pooler.c-3.us-east-1.aws.neon.tech',
    'port': 5432
}

def get_connection_string():
    """Returns PostgreSQL connection string"""
    return (f"dbname={DB_CONFIG['dbname']} "
            f"user={DB_CONFIG['user']} "
            f"password={DB_CONFIG['password']} "
            f"host={DB_CONFIG['host']} "
            f"port={DB_CONFIG['port']}")


# ============================================
# DATA GENERATION CONFIGURATION
# ============================================
DATA_CONFIG = {
    'nb_departements': 4,
    'nb_specializations_per_dept': 2,
    'nb_formations_per_spec': 5,
    'nb_groups_per_formation': 2,
    'nb_modules_per_formation': 4,
    'nb_professeurs_per_dept': 10,
    'nb_etudiants_per_group': 25,
    'nb_exam_locations': 50,
}



OPTIMIZATION_CONFIG = {
    'max_exams_per_day_student': 1,
    'max_exams_per_day_professor': 3,
    'exam_duration_options': [90],
    'exam_start_hours': [8, 10, 13, 15, 17],  # 5 slots
    'num_days': 28,  # ← INCREASED from 21 to 28 days (4 weeks)
    'start_date': '2026-02-01',
    'max_optimization_time_seconds': 120,
    'surveillants_per_exam': 1,
}


SYSTEM_CONFIG = {
    'debug_mode': True,
    'log_level': 'INFO',
    'max_scheduling_attempts': 3,
}