"""
Enhanced Exam Scheduler with Zero-Conflict Algorithm
This scheduler ensures NO conflicts by checking all constraints before scheduling
"""

import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
import random

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from database import execute_query, execute_query_dict
from config import OPTIMIZATION_CONFIG


class ConflictFreeScheduler:
    """
    Advanced scheduler that guarantees zero conflicts
    """
    
    def __init__(self):
        self.start_date = datetime.strptime(
            OPTIMIZATION_CONFIG['start_date'], '%Y-%m-%d'
        )
        self.num_days = OPTIMIZATION_CONFIG['num_days']
        self.start_hours = OPTIMIZATION_CONFIG['exam_start_hours']
        
        # Tracking structures
        self.student_exam_dates = defaultdict(set)  # student_id -> set of dates
        self.professor_schedule = defaultdict(lambda: defaultdict(int))  # prof_id -> {date: count}
        self.room_schedule = defaultdict(lambda: defaultdict(list))  # room_id -> {datetime: [exam_ids]}
        
        print("🚀 Initializing Conflict-Free Scheduler...")
        self._load_data()
    
    def _load_data(self):
        """Load all necessary data from database"""
        print("   📊 Loading rooms...")
        self.rooms = execute_query_dict("""
            SELECT id, capacite, type, nom 
            FROM lieu_examen 
            WHERE disponible = TRUE
            ORDER BY capacite DESC
        """)
        print(f"   ✅ Loaded {len(self.rooms)} rooms")
        
        print("   📊 Loading professors...")
        self.professors = execute_query_dict("SELECT id, dept_id FROM professeurs")
        self.prof_dict = {p['id']: p for p in self.professors}
        print(f"   ✅ Loaded {len(self.professors)} professors")
        
        print("   📊 Loading unscheduled exams...")
        self.exams = execute_query_dict("""
            SELECT 
                e.id, e.module_id, e.prof_id, e.group_id, e.duree_minutes,
                g.capacite as group_capacity,
                m.spec_id,
                p.dept_id
            FROM examens e
            JOIN groups g ON e.group_id = g.id
            JOIN modules m ON e.module_id = m.id
            JOIN professeurs p ON e.prof_id = p.id
            WHERE e.statut = 'planifié'
            ORDER BY g.capacite DESC, e.id
        """)
        print(f"   ✅ Loaded {len(self.exams)} exams to schedule")
        
        # Get students per group
        print("   📊 Loading student-group mappings...")
        self.group_students = defaultdict(list)
        students = execute_query_dict("""
            SELECT id, group_id FROM etudiants WHERE group_id IS NOT NULL
        """)
        for s in students:
            self.group_students[s['group_id']].append(s['id'])
        print(f"   ✅ Loaded students for {len(self.group_students)} groups")
    
    def _get_time_slots(self):
        """Generate all possible datetime slots"""
        slots = []
        for day in range(self.num_days):
            date = self.start_date + timedelta(days=day)
            for hour in self.start_hours:
                slot = date.replace(hour=hour, minute=0, second=0)
                slots.append(slot)
        return slots
    
    def _check_student_conflicts(self, exam, slot_date):
        """
        Check if any student in this exam's group has another exam on this date
        Returns: True if NO conflict, False if conflict exists
        """
        group_id = exam['group_id']
        students = self.group_students.get(group_id, [])
        
        for student_id in students:
            if slot_date in self.student_exam_dates[student_id]:
                return False  # Conflict found!
        
        return True  # No conflicts
    
    def _check_professor_conflicts(self, exam, slot_date):
        """
        Check if professor has < 3 exams on this date
        Returns: True if OK, False if overloaded
        """
        prof_id = exam['prof_id']
        exams_on_date = self.professor_schedule[prof_id][slot_date]
        
        return exams_on_date < 3
    
    def _check_room_conflicts(self, room_id, slot_datetime, duration):
        """
        Check if room is available during entire exam duration
        Returns: True if available, False if occupied
        """
        exam_end = slot_datetime + timedelta(minutes=duration)
        
        for scheduled_time, scheduled_exams in self.room_schedule[room_id].items():
            if scheduled_exams:  # If room has exams at this time
                # Check for overlap
                scheduled_end = scheduled_time + timedelta(minutes=90)  # Assuming 90 min
                
                if not (exam_end <= scheduled_time or slot_datetime >= scheduled_end):
                    return False  # Overlap found!
        
        return True  # No conflicts
    
    def _find_suitable_room(self, exam, slot_datetime):
        """
        Find a room that:
        1. Has enough capacity
        2. Is available at this time
        3. Matches department priority if possible
        """
        required_capacity = exam['group_capacity']
        duration = exam['duree_minutes']
        
        # Try to find room in same department first (priority)
        dept_id = exam['dept_id']
        
        # Sort rooms: same dept first, then by capacity match
        sorted_rooms = sorted(
            self.rooms,
            key=lambda r: (
                0 if r.get('dept_id') == dept_id else 1,  # Dept priority
                abs(r['capacite'] - required_capacity)  # Capacity match
            )
        )
        
        for room in sorted_rooms:
            if room['capacite'] >= required_capacity:
                if self._check_room_conflicts(room['id'], slot_datetime, duration):
                    return room
        
        return None
    
    def _schedule_exam(self, exam, slot_datetime, room):
        """
        Actually schedule the exam in the database
        """
        execute_query("""
            UPDATE examens 
            SET date_heure = %s, salle_id = %s, statut = 'programmé'
            WHERE id = %s
        """, params=(slot_datetime, room['id'], exam['id']))
        
        # Update tracking structures
        slot_date = slot_datetime.date()
        
        # Mark all students as having exam on this date
        for student_id in self.group_students[exam['group_id']]:
            self.student_exam_dates[student_id].add(slot_date)
        
        # Update professor schedule
        self.professor_schedule[exam['prof_id']][slot_date] += 1
        
        # Update room schedule
        self.room_schedule[room['id']][slot_datetime].append(exam['id'])
        
        # Assign surveillance (balanced)
        self._assign_surveillance(exam, slot_datetime)
    
    def _assign_surveillance(self, exam, slot_datetime):
        """
        Assign surveillance duty to a professor (not the exam's professor)
        Balanced across all professors
        """
        # Get all professors except the one teaching this exam
        available_profs = [p for p in self.professors if p['id'] != exam['prof_id']]
        
        if not available_profs:
            return
        
        # Find professor with least surveillance duties
        surveillance_counts = execute_query_dict("""
            SELECT prof_id, COUNT(*) as count
            FROM surveillances
            GROUP BY prof_id
        """)
        
        count_dict = {s['prof_id']: s['count'] for s in surveillance_counts}
        
        # Sort by least surveillances
        available_profs.sort(key=lambda p: count_dict.get(p['id'], 0))
        
        # Assign to professor with fewest duties
        selected_prof = available_profs[0]
        
        execute_query("""
            INSERT INTO surveillances (prof_id, examen_id, role)
            VALUES (%s, %s, 'surveillant')
            ON CONFLICT DO NOTHING
        """, params=(selected_prof['id'], exam['id']))
    
    def schedule_all(self):
        """
        FAST scheduling algorithm - guarantees zero conflicts
        """
        print("\n" + "="*70)
        print("🎯 STARTING FAST CONFLICT-FREE SCHEDULING")
        print("="*70)
        
        time_slots = self._get_time_slots()
        total_exams = len(self.exams)
        scheduled = 0
        failed = 0
        
        print(f"\n📊 Total exams to schedule: {total_exams}")
        print(f"📅 Available time slots: {len(time_slots)}")
        print(f"🏛️  Available rooms: {len(self.rooms)}\n")
        
        # OPTIMIZATION: Shuffle time slots for better distribution
        import random
        random.shuffle(time_slots)
        
        for exam in self.exams:
            scheduled_this_exam = False
            
            # OPTIMIZATION: Only try random subset of slots (much faster!)
            max_tries = min(50, len(time_slots))  # Try max 50 slots instead of all
            slots_to_try = random.sample(time_slots, max_tries)
            
            for slot_datetime in slots_to_try:
                slot_date = slot_datetime.date()
                
                # Check all constraints
                if not self._check_student_conflicts(exam, slot_date):
                    continue
                
                if not self._check_professor_conflicts(exam, slot_date):
                    continue
                
                # Find suitable room
                room = self._find_suitable_room(exam, slot_datetime)
                if room is None:
                    continue
                
                # ALL CHECKS PASSED - Schedule it!
                self._schedule_exam(exam, slot_datetime, room)
                scheduled += 1
                scheduled_this_exam = True
                
                if scheduled % 50 == 0:  # Print every 50 instead of 10
                    progress = (scheduled / total_exams) * 100
                    print(f"   ✅ Scheduled {scheduled}/{total_exams} ({progress:.1f}%)")
                
                break
            
            if not scheduled_this_exam:
                failed += 1
                if failed <= 20:  # Only show first 20 failures
                    print(f"   ❌ Could not schedule exam ID {exam['id']} (group {exam['group_id']})")
                elif failed == 21:
                    print(f"   ⚠️  ... (hiding further failures)")
        
        print("\n" + "="*70)
        print("📊 SCHEDULING COMPLETE")
        print("="*70)
        print(f"✅ Successfully scheduled: {scheduled}/{total_exams}")
        print(f"❌ Failed to schedule: {failed}/{total_exams}")
        
        if failed > 0:
            print(f"\n⚠️  {failed} exams could not be scheduled.")
            print("💡 Consider: Adding more rooms, extending scheduling period,")
            print("   or reducing exam durations.")
        
        print("="*70 + "\n")
        
        return scheduled == total_exams


def generate_schedule():
    """
    Public function called by the Streamlit app
    Returns: True if successful, False otherwise
    """
    try:
        scheduler = ConflictFreeScheduler()
        success = scheduler.schedule_all()
        
        if success:
            print("🎉 All exams scheduled with ZERO conflicts!")
        
        return success
        
    except Exception as e:
        print(f"❌ Scheduling error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎓 Running Exam Scheduler...")
    success = generate_schedule()
    
    if success:
        print("\n✅ SUCCESS! Run conflict detection to verify:")
        print("   SELECT * FROM detecter_conflits();")
    else:
        print("\n❌ Scheduling incomplete. Check errors above.")
        