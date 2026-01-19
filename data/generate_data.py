
import sys
import os

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

import psycopg2
from datetime import datetime
import random
import time

from config import get_connection_string, DATA_CONFIG, OPTIMIZATION_CONFIG

# Templates
DEPARTMENTS = [
    ('Computer Science', 'CS'),
    ('Mathematics', 'MATH'),
    ('Physics', 'PHYS'),
    ('Chemistry', 'CHEM'),
    ('Biology', 'BIO'),
    ('Economics', 'ECON'),
    ('Management', 'MGMT')
]

FIRST_NAMES = [
    'Ahmed', 'Fatima', 'Ali', 'Sara', 'Omar', 'Amina', 
    'Youssef', 'Nour', 'Karim', 'Meriem', 'Hassan', 'Rania',
    'Mehdi', 'Yasmine', 'Tarek', 'Samia', 'Amine', 'Khadija'
]

LAST_NAMES = [
    'Benali', 'Cherif', 'Kamel', 'Nasri', 'Rachid', 'Saidi',
    'Larbi', 'Mansour', 'Ghali', 'Hamdani', 'Djelloul', 'Farah',
    'Idrissi', 'Jaber', 'Ouali', 'Tahri', 'Bouzid', 'Essalhi'
]

MODULE_NAMES = [
    'Algorithms', 'Data Structures', 'Databases', 'Networks',
    'Web Development', 'AI', 'Machine Learning', 'Security',
    'Operating Systems', 'Software Engineering', 'Calculus',
    'Linear Algebra', 'Statistics', 'Probability', 'Physics',
    'Chemistry', 'Biology', 'Economics', 'Management', 'Marketing'
]

ROOM_TYPES = {
    'Amphitheater': (150, 300),
    'Classroom': (30, 60),
    'Lab': (20, 40),
    'Small Room': (15, 30)
}

def clear_all_tables(cur):
    print("🗑️  Clearing existing data...")
    tables = [
        'surveillances', 'conflits', 'examens', 'inscriptions',
        'modules', 'professeurs', 'etudiants', 'lieu_examen',
        'groups', 'formations', 'specializations', 'departements'
    ]
    for table in tables:
        cur.execute(f"DELETE FROM {table}")
        print(f"   ✓ {table}")
    print()

def print_config():
    print("📋 GENERATION CONFIGURATION:")
    print(f"   • Departments: {DATA_CONFIG['nb_departements']}")
    print(f"   • Specializations/dept: {DATA_CONFIG['nb_specializations_per_dept']}")
    print(f"   • Formations/spec: {DATA_CONFIG['nb_formations_per_spec']}")
    print(f"   • Groups/formation: {DATA_CONFIG['nb_groups_per_formation']}")
    print(f"   • Modules/formation: {DATA_CONFIG['nb_modules_per_formation']}")
    print(f"   • Students/group: {DATA_CONFIG['nb_etudiants_per_group']}")
    print(f"   • Professors/dept: {DATA_CONFIG['nb_professeurs_per_dept']}")
    print(f"   • Rooms: {DATA_CONFIG['nb_exam_locations']}")
    print(f"   • Exam duration: 90 minutes (ALL EXAMS)")  # ADDED
    
    total_specs = DATA_CONFIG['nb_departements'] * DATA_CONFIG['nb_specializations_per_dept']
    total_formations = total_specs * DATA_CONFIG['nb_formations_per_spec']
    total_groups = total_formations * DATA_CONFIG['nb_groups_per_formation']
    total_students = total_groups * DATA_CONFIG['nb_etudiants_per_group']
    total_exams = total_groups * DATA_CONFIG['nb_modules_per_formation']
    
    print(f"\n📊 ESTIMATED TOTALS:")
    print(f"   • Formations: {total_formations}")
    print(f"   • Groups: {total_groups}")
    print(f"   • Students: {total_students:,}")
    print(f"   • Exams: {total_exams:,}")
    
    slots = OPTIMIZATION_CONFIG['num_days'] * len(OPTIMIZATION_CONFIG['exam_start_hours'])
    capacity = slots * DATA_CONFIG['nb_exam_locations']
    utilization = (total_exams / capacity * 100) if capacity > 0 else 0
    
    print(f"\n🎯 SCHEDULING CAPACITY:")
    print(f"   • Time slots: {slots}")
    print(f"   • Total capacity: {capacity:,}")
    print(f"   • Utilization: {utilization:.1f}%")
    
    if utilization > 100:
        print(f"   ❌ OVERBOOKED! Need {total_exams - capacity} more slots")
    elif utilization > 80:
        print(f"   ⚠️  High utilization (>80%)")
    else:
        print(f"   ✅ Good capacity")
    
    print()

def generate_data(conn):
    cur = conn.cursor()
    clear_all_tables(cur)
    conn.commit()
    
    start_time = time.time()
    print("="*70)
    print("🚀 PROFESSIONAL DATA GENERATOR")
    print("="*70)
    print()
    print_config()
    
    # 1. Departments
    print("1️⃣  Creating departments...")
    dept_data = DEPARTMENTS[:DATA_CONFIG['nb_departements']]
    cur.executemany(
        "INSERT INTO departements (nom, code) VALUES (%s, %s)", 
        dept_data
    )
    conn.commit()
    cur.execute("SELECT id FROM departements ORDER BY id")
    dept_ids = [r[0] for r in cur.fetchall()]
    print(f"   ✅ {len(dept_ids)} departments\n")
    
    # 2. Specializations
    print("2️⃣  Creating specializations...")
    spec_data = []
    for dept_id in dept_ids:
        for i in range(DATA_CONFIG['nb_specializations_per_dept']):
            name = f"Specialization {i+1}"
            code = f"SPEC{dept_id:02d}{i+1:02d}"
            spec_data.append((name, dept_id, code))
    cur.executemany(
        "INSERT INTO specializations (nom, dept_id, code) VALUES (%s, %s, %s)",
        spec_data
    )
    conn.commit()
    cur.execute("SELECT id FROM specializations ORDER BY id")
    spec_ids = [r[0] for r in cur.fetchall()]
    print(f"   ✅ {len(spec_ids)} specializations\n")
    
    # 3. Formations
    print("3️⃣  Creating formations...")
    form_data = []
    levels = ['L1', 'L2', 'L3', 'M1', 'M2']
    for spec_id in spec_ids:
        for i in range(DATA_CONFIG['nb_formations_per_spec']):
            level = levels[i % len(levels)]
            name = f"Formation {level}"
            code = f"FORM{spec_id:03d}{i+1:02d}"
            form_data.append((
                name, spec_id, code, 
                DATA_CONFIG['nb_modules_per_formation'], level
            ))
    cur.executemany(
        """INSERT INTO formations (nom, spec_id, code, nb_modules, niveau) 
           VALUES (%s, %s, %s, %s, %s)""",
        form_data
    )
    conn.commit()
    cur.execute("SELECT id, nom FROM formations ORDER BY id")
    formations = cur.fetchall()
    print(f"   ✅ {len(formations)} formations\n")
    
    # 4. Groups - FIXED: Unique names per formation
    print("4️⃣  Creating groups (FIXED: unique names)...")
    group_data = []
    group_counter = 1  # Global counter for unique IDs
    
    for formation_id, formation_name in formations:
        for i in range(DATA_CONFIG['nb_groups_per_formation']):
            # FIXED: Use formation name + group letter for uniqueness
            group_letter = chr(65 + i)  # A, B, C, etc.
            group_name = f"{formation_name} - Group {group_letter}"
            capacity = DATA_CONFIG['nb_etudiants_per_group']
            group_data.append((group_name, formation_id, capacity))
            group_counter += 1
    
    cur.executemany(
        "INSERT INTO groups (nom, formation_id, capacite) VALUES (%s, %s, %s)",
        group_data
    )
    conn.commit()
    cur.execute("SELECT id, formation_id, nom FROM groups ORDER BY id")
    groups = cur.fetchall()
    print(f"   ✅ {len(groups)} groups (unique names)\n")
    
    # Show sample groups
    print("   📋 Sample group names:")
    for group_id, formation_id, group_name in groups[:5]:
        print(f"      - {group_name}")
    if len(groups) > 5:
        print(f"      ... and {len(groups) - 5} more")
    print()
    
    # 5. Modules
    print("5️⃣  Creating modules...")
    module_data = []
    for spec_id in spec_ids:
        cur.execute(
            "SELECT COUNT(*) FROM formations WHERE spec_id = %s", 
            (spec_id,)
        )
        num_formations = cur.fetchone()[0]
        num_modules = DATA_CONFIG['nb_modules_per_formation'] * num_formations
        
        for i in range(num_modules):
            name = random.choice(MODULE_NAMES)
            code = f"MOD{spec_id:03d}{i+1:03d}"
            credits = random.randint(3, 6)
            semester = random.choice([1, 2])
            module_data.append((name, code, credits, spec_id, semester))
    
    cur.executemany(
        """INSERT INTO modules (nom, code, credits, spec_id, semestre) 
           VALUES (%s, %s, %s, %s, %s)""",
        module_data
    )
    conn.commit()
    print(f"   ✅ {len(module_data)} modules\n")
    
    # 6. Professors
    print("6️⃣  Creating professors...")
    prof_data = []
    counter = 1
    for dept_id in dept_ids:
        for i in range(DATA_CONFIG['nb_professeurs_per_dept']):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            email = f"prof{counter}@university.dz"
            prof_data.append((last, first, dept_id, 'General', email))
            counter += 1
    cur.executemany(
        """INSERT INTO professeurs (nom, prenom, dept_id, specialite, email) 
           VALUES (%s, %s, %s, %s, %s)""",
        prof_data
    )
    conn.commit()
    print(f"   ✅ {len(prof_data)} professors\n")
    
    # 7. Exam Rooms
    print("7️⃣  Creating exam rooms...")
    room_data = []
    for i in range(DATA_CONFIG['nb_exam_locations']):
        room_type = random.choice(list(ROOM_TYPES.keys()))
        min_cap, max_cap = ROOM_TYPES[room_type]
        capacity = random.randint(min_cap, max_cap)
        name = f"{room_type} {i+1}"
        building = f"Building {chr(65 + i % 5)}"
        room_data.append((name, capacity, room_type, building))
    cur.executemany(
        """INSERT INTO lieu_examen (nom, capacite, type, batiment) 
           VALUES (%s, %s, %s, %s)""",
        room_data
    )
    conn.commit()
    print(f"   ✅ {DATA_CONFIG['nb_exam_locations']} rooms\n")
    
    # 8. Students
    print("8️⃣  Creating students...")
    student_data = []
    counter = 1
    for group_id, formation_id, group_name in groups:
        for i in range(DATA_CONFIG['nb_etudiants_per_group']):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            matricule = f"STU{counter:06d}"
            email = f"{first.lower()}.{last.lower()}{counter}@student.dz"
            student_data.append((
                last, first, matricule, group_id, 2024, email
            ))
            counter += 1
    cur.executemany(
        """INSERT INTO etudiants 
           (nom, prenom, matricule, group_id, promo, email) 
           VALUES (%s, %s, %s, %s, %s, %s)""",
        student_data
    )
    conn.commit()
    print(f"   ✅ {len(student_data):,} students\n")
    
    # 9. Enrollments
    print("9️⃣  Creating enrollments...")
    cur.execute("SELECT id, group_id FROM etudiants")
    students = cur.fetchall()
    
    cur.execute("""
        SELECT g.id as group_id, m.id as module_id
        FROM groups g
        JOIN formations f ON g.formation_id = f.id
        JOIN modules m ON f.spec_id = m.spec_id
    """)
    group_modules = {}
    for gid, mid in cur.fetchall():
        if gid not in group_modules:
            group_modules[gid] = []
        group_modules[gid].append(mid)
    
    enroll_data = []
    for student_id, group_id in students:
        available_modules = group_modules.get(group_id, [])
        num_to_enroll = min(
            random.randint(4, 8), 
            len(available_modules)
        )
        selected = random.sample(available_modules, num_to_enroll)
        
        for module_id in selected:
            note = round(random.uniform(10, 20), 2) if random.random() > 0.3 else None
            enroll_data.append((student_id, module_id, note, '2025-2026'))
    
    cur.executemany(
        """INSERT INTO inscriptions 
           (etudiant_id, module_id, note, annee_academique) 
           VALUES (%s, %s, %s, %s)""",
        enroll_data
    )
    conn.commit()
    print(f"   ✅ {len(enroll_data):,} enrollments\n")
    
     # 10. Exams - FIXED: All 90 minutes duration
    print("🔟 Creating unscheduled exams (ALL 90 minutes)...")
    
    cur.execute("""
        SELECT DISTINCT g.id as group_id, m.id as module_id, f.spec_id
        FROM groups g
        JOIN formations f ON g.formation_id = f.id
        JOIN modules m ON f.spec_id = m.spec_id
    """)
    group_module_pairs = cur.fetchall()
    
    exam_data = []
    cur.execute("SELECT id FROM professeurs")
    prof_list = [p[0] for p in cur.fetchall()]
    exam_types = ['Midterm', 'Final', 'Makeup']
    
    for group_id, module_id, spec_id in group_module_pairs:
        prof_id = random.choice(prof_list)
        duration = 90  # FIXED: Always 90 minutes!
        exam_type = random.choice(exam_types)
        
        exam_data.append((
            module_id, prof_id, None, group_id, None,
            duration, exam_type, True, 'planifié'
        ))
    
    cur.executemany(
        """INSERT INTO examens 
           (module_id, prof_id, salle_id, group_id, date_heure,
            duree_minutes, type_examen, priorite_dept, statut)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        exam_data
    )
    conn.commit()
    print(f"   ✅ {len(exam_data):,} exams (ALL 90 minutes)\n")
    
    cur.close()
    
    # Final summary
    elapsed = time.time() - start_time
    print("="*70)
    print("✅ DATA GENERATION COMPLETE")
    print("="*70)
    print(f"⏱️  Time: {elapsed:.2f} seconds")
    print(f"📊 Total records: {len(student_data) + len(enroll_data) + len(exam_data):,}")
    print(f"📅 Exams to schedule: {len(exam_data):,}")
    print(f"⏱️  All exams: 90 minutes duration")
    print("="*70)
    print("\n💡 Next steps:")
    print("   1. Run scheduler: python backend/scheduler.py")
    print("   2. Or launch app: streamlit run frontend/app.py")
    print("="*70 + "\n")

def main():
    print("="*70)
    print("🎓 EXAM SCHEDULING SYSTEM - DATA GENERATOR")
    print("="*70)
    print("\n⚠️  WARNING: This will DELETE all existing data!\n")
    
    response = input("Generate data? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    try:
        print("\n🔌 Connecting to database...")
        conn = psycopg2.connect(get_connection_string())
        print("✅ Connected!\n")
        
        generate_data(conn)
        conn.close()
        
        print("🎉 SUCCESS! Database populated with test data.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
