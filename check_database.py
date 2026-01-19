"""
Quick Diagnostic Script
Run this to check your database
Save as: check_database.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import execute_query_dict, execute_query

print("="*70)
print("🔍 DATABASE DIAGNOSTIC")
print("="*70)

# 1. Check exam durations
print("\n1️⃣ EXAM DURATIONS:")
durations = execute_query_dict("""
    SELECT duree_minutes, COUNT(*) as count
    FROM examens
    GROUP BY duree_minutes
    ORDER BY duree_minutes
""")
if durations:
    for d in durations:
        print(f"   {d['duree_minutes']} minutes: {d['count']} exams")
else:
    print("   ❌ No exams found!")

# 2. Check scheduled exams
print("\n2️⃣ EXAM STATUS:")
status = execute_query_dict("""
    SELECT statut, COUNT(*) as count
    FROM examens
    GROUP BY statut
""")
if status:
    for s in status:
        print(f"   {s['statut']}: {s['count']} exams")

# 3. Check a sample exam with full details
print("\n3️⃣ SAMPLE SCHEDULED EXAM:")
sample = execute_query_dict("""
    SELECT 
        e.id,
        m.nom as module,
        e.duree_minutes,
        e.type_examen,
        TO_CHAR(e.date_heure, 'DD/MM/YYYY HH24:MI') as date_time,
        l.nom as room,
        e.statut
    FROM examens e
    JOIN modules m ON e.module_id = m.id
    LEFT JOIN lieu_examen l ON e.salle_id = l.id
    WHERE e.statut = 'programmé'
    LIMIT 5
""")
if sample:
    for exam in sample:
        print(f"\n   Exam {exam['id']}: {exam['module']}")
        print(f"   Duration: {exam['duree_minutes']} minutes")
        print(f"   Type: {exam['type_examen']}")
        print(f"   Date/Time: {exam['date_time']}")
        print(f"   Room: {exam['room']}")
else:
    print("   ❌ No scheduled exams!")

# 4. Check student-group-exam relationship
print("\n4️⃣ STUDENT-EXAM RELATIONSHIP:")
student_check = execute_query_dict("""
    SELECT 
        et.id as student_id,
        et.matricule,
        g.id as group_id,
        g.nom as group_name,
        COUNT(DISTINCT e.id) as scheduled_exams
    FROM etudiants et
    LEFT JOIN groups g ON et.group_id = g.id
    LEFT JOIN examens e ON g.id = e.group_id AND e.statut = 'programmé'
    GROUP BY et.id, et.matricule, g.id, g.nom
    LIMIT 5
""")
if student_check:
    for student in student_check:
        print(f"   {student['matricule']} ({student['group_name']}): {student['scheduled_exams']} exams")

# 5. Check inscriptions vs exams
print("\n5️⃣ INSCRIPTIONS CHECK:")
inscriptions = execute_query_dict("""
    SELECT 
        COUNT(DISTINCT etudiant_id) as students_enrolled,
        COUNT(DISTINCT module_id) as modules_enrolled,
        COUNT(*) as total_enrollments
    FROM inscriptions
""")
if inscriptions:
    i = inscriptions[0]
    print(f"   Students with enrollments: {i['students_enrolled']}")
    print(f"   Modules with enrollments: {i['modules_enrolled']}")
    print(f"   Total enrollments: {i['total_enrollments']}")

# 6. Check if students in groups have corresponding exams
print("\n6️⃣ GROUP-EXAM MAPPING:")
group_exam = execute_query_dict("""
    SELECT 
        g.id,
        g.nom as group_name,
        COUNT(DISTINCT et.id) as students,
        COUNT(DISTINCT e.id) as exams
    FROM groups g
    LEFT JOIN etudiants et ON g.id = et.group_id
    LEFT JOIN examens e ON g.id = e.group_id AND e.statut = 'programmé'
    GROUP BY g.id, g.nom
    ORDER BY g.id
""")
if group_exam:
    print(f"\n   {'Group':<20} {'Students':<12} {'Exams':<12}")
    print("   " + "-"*44)
    for group in group_exam:
        print(f"   {group['group_name']:<20} {group['students']:<12} {group['exams']:<12}")

print("\n" + "="*70)
print("✅ DIAGNOSTIC COMPLETE")
print("="*70)

print("\n💡 WHAT TO CHECK:")
print("   1. Durations should be: 60, 90, 120, 180 (NOT all 90!)")
print("   2. All exams should be 'programmé' status")
print("   3. Each student should have exams = their group's exams")
print("   4. All groups should have exams assigned")

print("\n🔧 IF DURATIONS ARE WRONG:")
print("   Run: UPDATE examens SET duree_minutes = (ARRAY[60,90,120,180])[1 + floor(random()*4)];")

print("\n🔧 IF STUDENTS HAVE NO EXAMS:")
print("   Check that students are in groups that have scheduled exams")
print("="*70)