
import sys
import os

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import time

from database import execute_query, execute_query_dict
from scheduler import generate_schedule

st.set_page_config(
    page_title="Exam Scheduling System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 24px; color: #764ba2; }
    .exam-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
    }
</style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.dept_id = None

def login_page():
    """Enhanced login page with all roles"""
    st.markdown('<div class="main-header">🎓 Exam Scheduling System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">University Exam Management Platform</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Login to Your Account")
        
        # Role selection with icons
        role = st.selectbox(
            "Select Your Role:",
            [
                "👨‍🎓 Student",
                "👨‍🏫 Professor", 
                "👔 Department Head",
                "🏛️ Vice-Doyen / Doyen",
                "⚙️ Administrator"
            ]
        )
        
        role_clean = role.split(" ", 1)[1]  # Remove emoji
        
        if role_clean == "Student":
            st.markdown("---")
            matricule = st.text_input(
                "📝 Student ID (Matricule):",
                placeholder="Enter your student ID (e.g., STU000001)",
                help="Find your student ID on your student card"
            )
            
            if st.button("🔓 Login", use_container_width=True, type="primary"):
                if matricule:
                    result = execute_query_dict(
                        "SELECT id, nom, prenom FROM etudiants WHERE matricule = %s",
                        params=(matricule,)
                    )
                    if result:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "Student"
                        st.session_state.user_id = result[0]['id']
                        st.session_state.user_name = f"{result[0]['prenom']} {result[0]['nom']}"
                        st.success(f"✅ Welcome back, {st.session_state.user_name}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid student ID. Please check and try again.")
                else:
                    st.warning("⚠️ Please enter your student ID")
        
        elif role_clean == "Professor":
            st.markdown("---")
            email = st.text_input(
                "📧 Email Address:",
                placeholder="Enter your university email",
                help="Use your official university email"
            )
            
            if st.button("🔓 Login", use_container_width=True, type="primary"):
                if email:
                    result = execute_query_dict(
                        "SELECT id, nom, prenom, dept_id FROM professeurs WHERE email = %s",
                        params=(email,)
                    )
                    if result:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "Professor"
                        st.session_state.user_id = result[0]['id']
                        st.session_state.dept_id = result[0]['dept_id']
                        st.session_state.user_name = f"Prof. {result[0]['prenom']} {result[0]['nom']}"
                        st.success(f"✅ Welcome back, {st.session_state.user_name}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid email address")
                else:
                    st.warning("⚠️ Please enter your email")
        
        elif role_clean == "Department Head":
            st.markdown("---")
            
            # Get departments
            depts = execute_query_dict("SELECT id, nom FROM departements ORDER BY nom") or []
            dept_names = {d['nom']: d['id'] for d in depts}

            
            selected_dept = st.selectbox(
                "🏢 Select Your Department:",
                list(dept_names.keys())
            )
            
            password = st.text_input(
                "🔑 Access Code:",
                type="password",
                placeholder="Enter department head code"
            )
            
            if st.button("🔓 Login", use_container_width=True, type="primary"):
                if password == "dept123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Department Head"
                    st.session_state.user_id = dept_names[selected_dept]
                    st.session_state.dept_id = dept_names[selected_dept]
                    st.session_state.user_name = f"Head of {selected_dept}"
                    st.success(f"✅ Welcome, {st.session_state.user_name}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid access code")
        
        elif "Doyen" in role_clean:
            st.markdown("---")
            password = st.text_input(
                "🔑 Doyen Access Key:",
                type="password",
                placeholder="Enter doyen password"
            )
            
            if st.button("🔓 Login", use_container_width=True, type="primary"):
                if password == "doyen123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Doyen"
                    st.session_state.user_id = 1
                    st.session_state.user_name = "Monsieur le Doyen"
                    st.success("✅ Welcome, Monsieur le Doyen!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid access key")
        
        else:  # Administrator
            st.markdown("---")
            username = st.text_input(
                "👤 Username:",
                placeholder="Enter admin username"
            )
            password = st.text_input(
                "🔑 Password:",
                type="password",
                placeholder="Enter admin password"
            )
            
            if st.button("🔓 Login", use_container_width=True, type="primary"):
                if username == "admin" and password == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Administrator"
                    st.session_state.user_id = 1
                    st.session_state.user_name = "System Administrator"
                    st.success("✅ Welcome, Administrator!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        # Demo credentials
        with st.expander("📝 Demo Credentials & Help"):
            st.markdown("""
            **Student Login:**
            - Student ID: `STU000001` to `STU000400`
            
            **Professor Login:**
            - Email: `prof1@university.dz` to `prof10@university.dz`
            
            **Department Head:**
            - Choose any department
            - Password: `dept123`
            
            **Doyen:**
            - Password: `doyen123`
            
            **Administrator:**
            - Username: `admin`
            - Password: `admin123`
            """)

# ==========================================
# STUDENT PAGES
# ==========================================

def show_student_schedule():
    """Student personal exam schedule"""
    st.markdown("## 📅 My Exam Schedule")
    
    # Get student info
    student_info = execute_query_dict(
        """SELECT e.matricule, e.nom, e.prenom, g.nom as group_name, f.nom as formation
           FROM etudiants e
           JOIN groups g ON e.group_id = g.id
           JOIN formations f ON g.formation_id = f.id
           WHERE e.id = %s""",
        params=(st.session_state.user_id,)
    )
    
    if student_info:
        info = student_info[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**👤 Name:** {info['prenom']} {info['nom']}")
        with col2:
            st.info(f"**🎓 Formation:** {info['formation']}")
        with col3:
            st.info(f"**👥 Group:** {info['group_name']}")
    
    st.markdown("---")
    
    # Get exams
    query = """
        SELECT 
            TO_CHAR(e.date_heure, 'DD/MM/YYYY') as exam_date,
            TO_CHAR(e.date_heure, 'HH24:MI') as exam_time,
            TO_CHAR(e.date_heure, 'Day') as day_name,
            m.nom as module,
            m.credits,
            e.duree_minutes as duration,
            l.nom as room,
            l.batiment as building,
            l.type as room_type,
            e.type_examen as exam_type,
            p.prenom || ' ' || p.nom as professor,
            e.date_heure
        FROM etudiants et
        JOIN groups g ON et.group_id = g.id
        JOIN examens e ON g.id = e.group_id
        JOIN modules m ON e.module_id = m.id
        JOIN lieu_examen l ON e.salle_id = l.id
        JOIN professeurs p ON e.prof_id = p.id
        WHERE et.id = %s 
        AND e.date_heure IS NOT NULL
        AND e.statut = 'programmé'
        ORDER BY e.date_heure
    """
    
    df = pd.DataFrame(execute_query_dict(query, params=(st.session_state.user_id,)))
    
    if not df.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Total Exams", len(df))
        with col2:
            total_hours = df['duration'].sum() / 60
            st.metric("⏱️ Total Duration", f"{total_hours:.1f}h")
        with col3:
            today = date.today()
            upcoming = df[pd.to_datetime(df['date_heure']).dt.date >= today]
            st.metric("📅 Upcoming", len(upcoming))
        with col4:
            if not df.empty:
                first_date = pd.to_datetime(df['date_heure']).min().strftime('%d/%m/%Y')
                st.metric("🗓️ First Exam", first_date)
        
        st.markdown("---")
        
        # Display exams as cards
        for idx, row in df.iterrows():
            exam_date = pd.to_datetime(row['date_heure']).date()
            is_upcoming = exam_date >= date.today()
            
            status_color = "#4CAF50" if is_upcoming else "#9E9E9E"
            status_text = "📍 Upcoming" if is_upcoming else "✅ Completed"
            
            st.markdown(f"""
            <div style='border-left: 4px solid {status_color}; padding: 15px; margin: 10px 0; 
                        background: bleu; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='display: flex; justify-content: space-between;'>
                    <div>
                        <h3 style='margin: 0; color: #333;'>📚 {row['module']}</h3>
                        <p style='color: #666; margin: 5px 0;'>{row['exam_type']} • {row['credits']} credits</p>
                    </div>
                    <div style='text-align: right;'>
                        <span style='background: {status_color}; color: white; padding: 5px 10px; 
                                     border-radius: 15px; font-size: 0.9em;'>{status_text}</span>
                    </div>
                </div>
                <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;'>
                    <div>
                        <strong>📅 Date:</strong><br>{row['exam_date']}<br>
                        <small style='color: #666;'>{row['day_name'].strip()}</small>
                    </div>
                    <div>
                        <strong>🕐 Time:</strong><br>{row['exam_time']}<br>
                        <small style='color: #666;'>{row['duration']} minutes</small>
                    </div>
                    <div>
                        <strong>🏛️ Location:</strong><br>{row['room']}<br>
                        <small style='color: #666;'>{row['building']}</small>
                    </div>
                </div>
                <div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;'>
                    <strong>👨‍🏫 Professor:</strong> {row['professor']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Export button
        st.markdown("---")
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download My Schedule (CSV)",
            csv,
            "my_exam_schedule.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.warning("📋 No exams scheduled yet for your group")

def show_student_results():
    """Student results - FIXED: Beautiful display with proper data"""
    st.markdown("## 📊 My Exam Results")
    
    # Get student's group info
    student_info = execute_query_dict("""
        SELECT e.id, e.group_id, g.nom as group_name
        FROM etudiants e
        JOIN groups g ON e.group_id = g.id
        WHERE e.id = %s
    """, params=(st.session_state.user_id,))
    
    if not student_info:
        st.error("Could not load student information")
        return
    
    group_id = student_info[0]['group_id']
    
    # Get exams for this student's group
    query = """
        SELECT 
            m.nom as module,
            m.code as module_code,
            m.credits,
            e.date_heure as exam_date,
            e.type_examen as exam_type,
            i.note as grade,
            p.prenom || ' ' || p.nom as professor,
            CASE 
                WHEN e.date_heure > CURRENT_TIMESTAMP THEN 'upcoming'
                WHEN e.date_heure IS NULL THEN 'not_scheduled'
                WHEN i.note IS NULL THEN 'pending'
                WHEN i.note >= 10 THEN 'passed'
                ELSE 'failed'
            END as status
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN professeurs p ON e.prof_id = p.id
        LEFT JOIN inscriptions i ON i.module_id = e.module_id 
            AND i.etudiant_id = %s
        WHERE e.group_id = %s
        ORDER BY 
            CASE 
                WHEN e.date_heure IS NULL THEN 1
                ELSE 0
            END,
            e.date_heure DESC
    """
    
    results = execute_query_dict(query, params=(st.session_state.user_id, group_id))
    
    if not results:
        st.warning("📋 No exam results available yet")
        return
    
    # Calculate metrics
    past_exams = [r for r in results if r['status'] in ['passed', 'failed', 'pending']]
    graded_exams = [r for r in results if r['grade'] is not None and r['grade'] > 0]
    passed_exams = [r for r in graded_exams if r['grade'] >= 10]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Total Exams", len(results))
    
    with col2:
        if graded_exams:
            avg_grade = sum(r['grade'] for r in graded_exams) / len(graded_exams)
            st.metric("📊 Average Grade", f"{avg_grade:.2f}/20")
        else:
            st.metric("📊 Average Grade", "N/A")
    
    with col3:
        st.metric("✅ Passed", len(passed_exams))
    
    with col4:
        earned_credits = sum(r['credits'] for r in passed_exams)
        st.metric("🎓 Credits Earned", int(earned_credits))
    
    st.markdown("---")
    
    # Display results by status
    upcoming = [r for r in results if r['status'] == 'upcoming']
    pending = [r for r in results if r['status'] == 'pending']
    graded = [r for r in results if r['status'] in ['passed', 'failed']]
    not_scheduled = [r for r in results if r['status'] == 'not_scheduled']
    
    # Tabs for organization
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📊 Graded ({len(graded)})",
        f"⏳ Pending ({len(pending)})",
        f"📅 Upcoming ({len(upcoming)})",
        f"🕐 Not Scheduled ({len(not_scheduled)})"
    ])
    
    with tab1:
        if graded:
            for exam in graded:
                color = "#4CAF50" if exam['status'] == 'passed' else "#F44336"
                status_icon = "✅" if exam['status'] == 'passed' else "❌"
                status_text = "PASSED" if exam['status'] == 'passed' else "FAILED"
                
                st.markdown(f"""
                <div style='border-left: 5px solid {color}; padding: 20px; margin: 15px 0; 
                            background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div style='flex: 1;'>
                            <h3 style='margin: 0; color: #333;'>📚 {exam['module']}</h3>
                            <p style='color: #666; margin: 5px 0;'>
                                {exam['module_code']} • {exam['exam_type']} • {exam['credits']} credits
                            </p>
                            <p style='color: #888; margin: 5px 0; font-size: 0.9em;'>
                                👨‍🏫 {exam['professor']}
                            </p>
                        </div>
                        <div style='text-align: right; min-width: 120px;'>
                            <div style='font-size: 2em; font-weight: bold; color: {color};'>
                                {exam['grade']:.2f}/20
                            </div>
                            <div style='background: {color}; color: white; padding: 5px 15px; 
                                        border-radius: 20px; font-size: 0.85em; margin-top: 8px;'>
                                {status_icon} {status_text}
                            </div>
                        </div>
                    </div>
                    <div style='margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee; 
                                font-size: 0.9em; color: #666;'>
                        📅 Exam Date: {exam['exam_date'].strftime('%d/%m/%Y %H:%M') if exam['exam_date'] else 'N/A'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No graded exams yet")
    
    with tab2:
        if pending:
            for exam in pending:
                st.markdown(f"""
                <div style='border-left: 5px solid #FF9800; padding: 20px; margin: 15px 0; 
                            background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                    <h3 style='margin: 0; color: #333;'>📚 {exam['module']}</h3>
                    <p style='color: #666; margin: 8px 0;'>
                        {exam['module_code']} • {exam['exam_type']} • {exam['credits']} credits
                    </p>
                    <p style='color: #888; margin: 5px 0;'>👨‍🏫 {exam['professor']}</p>
                    <div style='margin-top: 12px; padding: 10px; background: #FFF3E0; 
                                border-radius: 5px; color: #E65100;'>
                        ⏳ Grade pending - Exam taken on {exam['exam_date'].strftime('%d/%m/%Y')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No pending results")
    
    with tab3:
        if upcoming:
            for exam in upcoming:
                st.markdown(f"""
                <div style='border-left: 5px solid #2196F3; padding: 20px; margin: 15px 0; 
                            background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                    <h3 style='margin: 0; color: #333;'>📚 {exam['module']}</h3>
                    <p style='color: #666; margin: 8px 0;'>
                        {exam['module_code']} • {exam['exam_type']} • {exam['credits']} credits
                    </p>
                    <p style='color: #888; margin: 5px 0;'>👨‍🏫 {exam['professor']}</p>
                    <div style='margin-top: 12px; padding: 10px; background: #E3F2FD; 
                                border-radius: 5px; color: #0D47A1;'>
                        📅 Scheduled for: {exam['exam_date'].strftime('%d/%m/%Y at %H:%M')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No upcoming exams")
    
    with tab4:
        if not_scheduled:
            for exam in not_scheduled:
                st.markdown(f"""
                <div style='border-left: 5px solid #9E9E9E; padding: 20px; margin: 15px 0; 
                            background: black ; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                    <h3 style='margin: 0; color: #333;'>📚 {exam['module']}</h3>
                    <p style='color: #666; margin: 8px 0;'>
                        {exam['module_code']} • {exam['exam_type']} • {exam['credits']} credits
                    </p>
                    <p style='color: #888; margin: 5px 0;'>👨‍🏫 {exam['professor']}</p>
                    <div style='margin-top: 12px; padding: 10px; background: #FAFAFA; 
                                border-radius: 5px; color: #616161;'>
                        🕐 Not yet scheduled
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ All exams are scheduled!")
    
    # Export button
    st.markdown("---")
    if graded:
        # Create downloadable CSV
        import pandas as pd
        df = pd.DataFrame([{
            'Module': r['module'],
            'Code': r['module_code'],
            'Credits': r['credits'],
            'Grade': r['grade'] if r['grade'] else 'N/A',
            'Status': r['status'].upper(),
            'Exam Type': r['exam_type'],
            'Date': r['exam_date'].strftime('%d/%m/%Y') if r['exam_date'] else 'N/A'
        } for r in graded])
        
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download Results (CSV)",
            csv,
            "my_exam_results.csv",
            "text/csv",
            use_container_width=True
        )

# ==========================================
# PROFESSOR PAGES
# ==========================================

def show_professor_schedule():
    """FIXED: Professor complete schedule"""
    st.markdown("## 📅 My Teaching Schedule")
    
    tab1, tab2, tab3 = st.tabs(["📚 Teaching", "👁️ Surveillance", "📊 Summary"])
    
    with tab1:
        st.subheader("Exams I'm Teaching")
        
        query = """
            SELECT 
                TO_CHAR(e.date_heure, 'DD/MM/YYYY HH24:MI') as datetime,
                m.nom as module,
                g.nom as group_name,
                l.nom as room,
                l.batiment as building,
                e.duree_minutes as duration,
                e.type_examen as exam_type,
                COUNT(DISTINCT et.id) as student_count
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN lieu_examen l ON e.salle_id = l.id
            JOIN groups g ON e.group_id = g.id
            LEFT JOIN etudiants et ON g.id = et.group_id
            WHERE e.prof_id = %s 
            AND e.date_heure IS NOT NULL
            AND e.statut = 'programmé'
            GROUP BY e.id, e.date_heure, m.nom, g.nom, l.nom, l.batiment, e.duree_minutes, e.type_examen
            ORDER BY e.date_heure
        """
        
        df = pd.DataFrame(execute_query_dict(query, params=(st.session_state.user_id,)))
        
        if not df.empty:
            st.success(f"✅ You are teaching {len(df)} exams")
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No teaching assignments yet")
    
    with tab2:
        st.subheader("Surveillance Duties")
        
        query = """
            SELECT 
                TO_CHAR(e.date_heure, 'DD/MM/YYYY HH24:MI') as datetime,
                m.nom as module,
                g.nom as group_name,
                l.nom as room,
                e.duree_minutes as duration,
                s.role
            FROM surveillances s
            JOIN examens e ON s.examen_id = e.id
            JOIN modules m ON e.module_id = m.id
            JOIN lieu_examen l ON e.salle_id = l.id
            JOIN groups g ON e.group_id = g.id
            WHERE s.prof_id = %s 
            AND e.date_heure IS NOT NULL
            AND e.statut = 'programmé'
            ORDER BY e.date_heure
        """
        
        df = pd.DataFrame(execute_query_dict(query, params=(st.session_state.user_id,)))
        
        if not df.empty:
            st.success(f"✅ You have {len(df)} surveillance duties")
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No surveillance assignments yet")
    
    with tab3:
        st.subheader("My Schedule Summary")
        
        # Get combined schedule
        total_teaching = execute_query(
            "SELECT COUNT(*) FROM examens WHERE prof_id = %s AND statut = 'programmé'",
            params=(st.session_state.user_id,),
            fetch=True
        )
        
        total_surveillance = execute_query(
            """SELECT COUNT(*) FROM surveillances s 
               JOIN examens e ON s.examen_id = e.id 
               WHERE s.prof_id = %s AND e.statut = 'programmé'""",
            params=(st.session_state.user_id,),
            fetch=True
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📚 Teaching", total_teaching[0][0] if total_teaching else 0)
        with col2:
            st.metric("👁️ Surveillance", total_surveillance[0][0] if total_surveillance else 0)
        with col3:
            total = (total_teaching[0][0] if total_teaching else 0) + (total_surveillance[0][0] if total_surveillance else 0)
            st.metric("📊 Total Duties", total)

# ==========================================
# DEPARTMENT HEAD PAGES
# ==========================================

def show_department_dashboard():
    """Department head dashboard"""
    st.markdown("## 🏢 Department Dashboard")
    
    # Get department info
    dept_info = execute_query_dict(
        "SELECT nom, code FROM departements WHERE id = %s",
        params=(st.session_state.dept_id,)
    )
    
    if dept_info:
        st.info(f"**Department:** {dept_info[0]['nom']} ({dept_info[0]['code']})")
    
    st.markdown("---")
    
    # Department statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        result = execute_query_dict("""
            SELECT COUNT(DISTINCT e.id) as count
            FROM etudiants e
            JOIN groups g ON e.group_id = g.id
            JOIN formations f ON g.formation_id = f.id
            JOIN specializations s ON f.spec_id = s.id
            WHERE s.dept_id = %s
        """, params=(st.session_state.dept_id,))
        st.metric("👨‍🎓 Students", result[0]['count'] if result else 0)
    
    with col2:
        result = execute_query_dict(
            "SELECT COUNT(*) as count FROM professeurs WHERE dept_id = %s",
            params=(st.session_state.dept_id,)
        )
        st.metric("👨‍🏫 Professors", result[0]['count'] if result else 0)
    
    with col3:
        result = execute_query_dict("""
            SELECT COUNT(DISTINCT e.id) as count
            FROM examens e
            JOIN groups g ON e.group_id = g.id
            JOIN formations f ON g.formation_id = f.id
            JOIN specializations s ON f.spec_id = s.id
            WHERE s.dept_id = %s AND e.statut = 'programmé'
        """, params=(st.session_state.dept_id,))
        st.metric("📝 Scheduled Exams", result[0]['count'] if result else 0)
    
    with col4:
        result = execute_query_dict("""
            SELECT COUNT(DISTINCT c.id) as count
            FROM conflits c
            JOIN examens e ON c.examen_id = e.id
            JOIN groups g ON e.group_id = g.id
            JOIN formations f ON g.formation_id = f.id
            JOIN specializations s ON f.spec_id = s.id
            WHERE s.dept_id = %s AND c.resolu = FALSE
        """, params=(st.session_state.dept_id,))
        st.metric("⚠️ Conflicts", result[0]['count'] if result else 0)
    
    st.markdown("---")
    
    # Department exams list
    st.subheader("📅 Department Exam Schedule")
    
    query = """
        SELECT 
            e.id,
            m.nom as module,
            p.prenom || ' ' || p.nom as professor,
            l.nom as room,
            g.nom as group_name,
            TO_CHAR(e.date_heure, 'DD/MM/YYYY HH24:MI') as date_time,
            e.duree_minutes as duration,
            e.statut as status
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN professeurs p ON e.prof_id = p.id
        LEFT JOIN lieu_examen l ON e.salle_id = l.id
        JOIN groups g ON e.group_id = g.id
        JOIN formations f ON g.formation_id = f.id
        JOIN specializations s ON f.spec_id = s.id
        WHERE s.dept_id = %s
        ORDER BY e.date_heure DESC NULLS LAST
        LIMIT 100
    """
    
    df = pd.DataFrame(execute_query_dict(query, params=(st.session_state.dept_id,)))
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No exams found for this department")

# ==========================================
# DOYEN PAGES - COMPLETE VERSION
# ==========================================

def show_doyen_dashboard():
    """Doyen strategic dashboard - Complete"""
    st.markdown("## 🏛️ Strategic Dashboard (Doyen)")
    st.markdown('<div class="sub-header">University-Wide Overview</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # University-wide statistics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        result = execute_query("SELECT COUNT(*) FROM etudiants", fetch=True)
        st.metric("👨‍🎓 Total Students", f"{result[0][0]:,}")
    
    with col2:
        result = execute_query("SELECT COUNT(*) FROM professeurs", fetch=True)
        st.metric("👨‍🏫 Total Professors", f"{result[0][0]:,}")
    
    with col3:
        result = execute_query("SELECT COUNT(*) FROM departements", fetch=True)
        st.metric("🏢 Departments", f"{result[0][0]:,}")
    
    with col4:
        result = execute_query(
            "SELECT COUNT(*) FROM examens WHERE statut = 'programmé'",
            fetch=True
        )
        st.metric("📝 Scheduled Exams", f"{result[0][0]:,}")
    
    with col5:
        result = execute_query(
            "SELECT COUNT(*) FROM conflits WHERE resolu = FALSE",
            fetch=True
        )
        conflicts = result[0][0] if result else 0
        st.metric("⚠️ Active Conflicts", conflicts, delta="Critical" if conflicts > 0 else "Good")
    
    st.markdown("---")
    
    # Progress Overview
    st.subheader("📊 Scheduling Progress")
    total_exams = execute_query("SELECT COUNT(*) FROM examens", fetch=True)
    scheduled_exams = execute_query("SELECT COUNT(*) FROM examens WHERE statut = 'programmé'", fetch=True)
    
    if total_exams and scheduled_exams:
        total = total_exams[0][0]
        scheduled = scheduled_exams[0][0]
        progress = (scheduled / total * 100) if total > 0 else 0
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(progress / 100)
        with col2:
            st.metric("Progress", f"{progress:.1f}%")
        
        st.caption(f"✅ {scheduled} out of {total} exams scheduled")
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Students by Department")
        query = """
            SELECT d.nom as department, COUNT(DISTINCT e.id) as count
            FROM departements d
            LEFT JOIN specializations s ON d.id = s.dept_id
            LEFT JOIN formations f ON s.id = f.spec_id
            LEFT JOIN groups g ON f.id = g.formation_id
            LEFT JOIN etudiants e ON g.id = e.group_id
            GROUP BY d.nom
            ORDER BY count DESC
        """
        df = pd.DataFrame(execute_query_dict(query))
        if not df.empty:
            fig = px.bar(
                df, 
                x='department', 
                y='count', 
                color='count',
                color_continuous_scale='Viridis',
                labels={'department': 'Department', 'count': 'Number of Students'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("📅 Exams Timeline")
        query = """
            SELECT DATE(date_heure) as date, COUNT(*) as count
            FROM examens
            WHERE date_heure IS NOT NULL
            GROUP BY DATE(date_heure)
            ORDER BY date
            LIMIT 30
        """
        df = pd.DataFrame(execute_query_dict(query))
        if not df.empty:
            fig = px.line(
                df, 
                x='date', 
                y='count', 
                markers=True,
                labels={'date': 'Date', 'count': 'Number of Exams'}
            )
            fig.update_traces(line_color='#667eea', marker=dict(size=8))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No scheduled exams yet")
    
    st.markdown("---")
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Exams by Department")
        query = """
            SELECT d.nom as department, COUNT(DISTINCT e.id) as exam_count
            FROM departements d
            LEFT JOIN specializations s ON d.id = s.dept_id
            LEFT JOIN formations f ON s.id = f.spec_id
            LEFT JOIN groups g ON f.id = g.formation_id
            LEFT JOIN examens e ON g.id = e.group_id
            WHERE e.statut = 'programmé'
            GROUP BY d.nom
            ORDER BY exam_count DESC
        """
        df = pd.DataFrame(execute_query_dict(query))
        if not df.empty:
            fig = px.pie(
                df, 
                values='exam_count', 
                names='department',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No exams scheduled yet")
    
    with col2:
        st.subheader("⚠️ Conflicts by Type")
        query = """
            SELECT type_conflit, COUNT(*) as count
            FROM conflits
            WHERE resolu = FALSE
            GROUP BY type_conflit
            ORDER BY count DESC
        """
        df = pd.DataFrame(execute_query_dict(query))
        if not df.empty:
            fig = px.bar(
                df, 
                x='type_conflit', 
                y='count',
                color='count',
                color_continuous_scale='Reds',
                labels={'type_conflit': 'Conflict Type', 'count': 'Number of Conflicts'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No active conflicts!")
    
    st.markdown("---")
    
    # Department Performance Table
    st.subheader("🏢 Department Performance Overview")
    query = """
        SELECT 
            d.nom as department,
            COUNT(DISTINCT e.id) as students,
            COUNT(DISTINCT p.id) as professors,
            COUNT(DISTINCT ex.id) as total_exams,
            COUNT(DISTINCT CASE WHEN ex.statut = 'programmé' THEN ex.id END) as scheduled_exams,
            COUNT(DISTINCT c.id) as conflicts
        FROM departements d
        LEFT JOIN professeurs p ON d.id = p.dept_id
        LEFT JOIN specializations s ON d.id = s.dept_id
        LEFT JOIN formations f ON s.id = f.spec_id
        LEFT JOIN groups g ON f.id = g.formation_id
        LEFT JOIN etudiants e ON g.id = e.group_id
        LEFT JOIN examens ex ON g.id = ex.group_id
        LEFT JOIN conflits c ON ex.id = c.examen_id AND c.resolu = FALSE
        GROUP BY d.nom
        ORDER BY students DESC
    """
    df = pd.DataFrame(execute_query_dict(query))
    
    if not df.empty:
        # Add completion percentage
        df['completion_%'] = ((df['scheduled_exams'] / df['total_exams'] * 100).fillna(0)).round(1)
        
        # Style the dataframe
        st.dataframe(
            df.style.background_gradient(subset=['students'], cmap='Blues')
                   .background_gradient(subset=['completion_%'], cmap='Greens')
                   .background_gradient(subset=['conflicts'], cmap='Reds'),
            use_container_width=True,
            height=300
        )
    else:
        st.info("No department data available")
    
    st.markdown("---")
    
    # Action Buttons for Doyen
    st.subheader("🎯 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("📄 Report generation feature coming soon!")
    
    with col2:
        if st.button("📧 Notify Departments", use_container_width=True):
            st.info("📧 Notification feature coming soon!")
    
    with col3:
        if st.button("🔍 View All Conflicts", use_container_width=True):
            # Show conflicts
            conflicts_query = """
                SELECT 
                    c.type_conflit,
                    m.nom as module,
                    TO_CHAR(e.date_heure, 'DD/MM/YYYY HH24:MI') as datetime,
                    c.description
                FROM conflits c
                JOIN examens e ON c.examen_id = e.id
                JOIN modules m ON e.module_id = m.id
                WHERE c.resolu = FALSE
                ORDER BY e.date_heure
                LIMIT 50
            """
            conflicts_df = pd.DataFrame(execute_query_dict(conflicts_query))
            if not conflicts_df.empty:
                st.dataframe(conflicts_df, use_container_width=True)
            else:
                st.success("✅ No conflicts to display!")
    
    with col4:
        if st.button("📥 Export Data", use_container_width=True):
            st.info("💾 Export feature coming soon!")
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📝 Recent Scheduling Activity")
    activity_query = """
        SELECT 
            m.nom as module,
            g.nom as group_name,
            TO_CHAR(e.date_heure, 'DD/MM/YYYY HH24:MI') as exam_datetime,
            l.nom as room,
            p.prenom || ' ' || p.nom as professor,
            e.statut as status
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN groups g ON e.group_id = g.id
        LEFT JOIN lieu_examen l ON e.salle_id = l.id
        JOIN professeurs p ON e.prof_id = p.id
        WHERE e.date_heure IS NOT NULL
        ORDER BY e.date_heure DESC
        LIMIT 20
    """
    activity_df = pd.DataFrame(execute_query_dict(activity_query))
    
    if not activity_df.empty:
        st.dataframe(activity_df, use_container_width=True, height=300)
    else:
        st.info("No recent activity")


# ==========================================
# ADMINISTRATOR PAGES
# ==========================================

def show_admin_dashboard():
    """Administrator main dashboard"""
    st.markdown('<div class="main-header">📊 System Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        result = execute_query("SELECT COUNT(*) FROM etudiants", fetch=True)
        count = result[0][0] if result else 0
        st.metric("👨‍🎓 Students", f"{count:,}")
    
    with col2:
        result = execute_query("SELECT COUNT(*) FROM professeurs", fetch=True)
        count = result[0][0] if result else 0
        st.metric("👨‍🏫 Professors", f"{count:,}")
    
    with col3:
        result = execute_query(
            "SELECT COUNT(*) FROM examens WHERE statut = 'programmé'",
            fetch=True
        )
        count = result[0][0] if result else 0
        st.metric("📝 Scheduled", f"{count:,}")
    
    with col4:
        result = execute_query(
            "SELECT COUNT(*) FROM conflits WHERE resolu = FALSE",
            fetch=True
        )
        conflicts = result[0][0] if result else 0
        st.metric("⚠️ Conflicts", conflicts, delta="Critical" if conflicts > 0 else "None")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Students by Department")
        query = """
            SELECT d.nom as department, COUNT(DISTINCT e.id) as count
            FROM departements d
            LEFT JOIN specializations s ON d.id = s.dept_id
            LEFT JOIN formations f ON s.id = f.spec_id
            LEFT JOIN groups g ON f.id = g.formation_id
            LEFT JOIN etudiants e ON g.id = e.group_id
            GROUP BY d.nom
            ORDER BY count DESC
        """
        df = pd.DataFrame(execute_query_dict(query))
        if not df.empty:
            fig = px.bar(df, x='department', y='count', color='count',
                        color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📅 Exams Timeline")
        query = """
            SELECT DATE(date_heure) as date, COUNT(*) as count
            FROM examens
            WHERE date_heure IS NOT NULL
            GROUP BY DATE(date_heure)
            ORDER BY date
            LIMIT 30
        """
        df = pd.DataFrame(execute_query_dict(query))
        if not df.empty:
            fig = px.line(df, x='date', y='count', markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    # Status overview
    st.markdown("---")
    status_query = """
        SELECT statut, COUNT(*) as count
        FROM examens
        GROUP BY statut
    """
    status_df = pd.DataFrame(execute_query_dict(status_query))
    
    if not status_df.empty:
        cols = st.columns(len(status_df))
        for idx, row in status_df.iterrows():
            with cols[idx]:
                st.metric(row['statut'].upper(), row['count'])

def show_admin_exams():
    """Administrator exam management"""
    st.markdown("## 📅 Exam Management")
    
    st.markdown("---")
    
    # Filters
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input("🔍 Search modules...")
    
    with col2:
        status = st.selectbox("Status Filter", ["All", "planifié", "programmé"])
    
    # Query
    query = """
        SELECT 
            e.id, m.nom as module, p.prenom || ' ' || p.nom as professor,
            COALESCE(l.nom, 'Not assigned') as room, g.nom as group_name,
            COALESCE(TO_CHAR(e.date_heure, 'DD/MM/YYYY HH24:MI'), 'Not scheduled') as date_time,
            e.duree_minutes as duration, e.statut as status
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN professeurs p ON e.prof_id = p.id
        LEFT JOIN lieu_examen l ON e.salle_id = l.id
        JOIN groups g ON e.group_id = g.id
        WHERE 1=1
    """
    
    params = []
    if search:
        query += " AND m.nom ILIKE %s"
        params.append(f"%{search}%")
    if status != "All":
        query += " AND e.statut = %s"
        params.append(status)
    
    query += " ORDER BY e.date_heure DESC NULLS LAST LIMIT 100"
    
    df = pd.DataFrame(execute_query_dict(query, params=params if params else None))
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No exams found matching your filters")
    
    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unscheduled = execute_query(
            "SELECT COUNT(*) FROM examens WHERE statut = 'planifié'",
            fetch=True
        )
        count = unscheduled[0][0] if unscheduled else 0
        
        if st.button("🔄 Generate Schedule", use_container_width=True, type="primary"):
            if count > 0:
                with st.spinner(f"Scheduling {count} exams..."):
                    success = generate_schedule()
                    if success:
                        st.success("✅ Schedule generated successfully!")
                        execute_query("SELECT detecter_conflits()")
                        time.sleep(2)
                        st.rerun()
            else:
                st.info("All exams are already scheduled!")
    
    with col2:
        if st.button("🔍 Detect Conflicts", use_container_width=True):
            with st.spinner("Detecting conflicts..."):
                execute_query("SELECT detecter_conflits()")
                st.success("✅ Conflict detection complete!")
                time.sleep(1)
                st.rerun()
    
    with col3:
        if st.button("🔄 Reset All Schedules", use_container_width=True):
            if st.session_state.get('confirm_reset'):
                with st.spinner("Resetting all schedules..."):
                    execute_query("UPDATE examens SET statut = 'planifié', date_heure = NULL, salle_id = NULL")
                    execute_query("DELETE FROM surveillances")
                    st.success("✅ All schedules reset!")
                    st.session_state.confirm_reset = False
                    time.sleep(1)
                    st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("⚠️ Click again to confirm reset")

# ==========================================
# SIDEBAR FUNCTION (FIXED!)
# ==========================================

def show_sidebar():
    """Enhanced sidebar with navigation"""
    with st.sidebar:
        st.title(f"👋 {st.session_state.user_name}")
        st.caption(f"Role: {st.session_state.user_role}")
        
        st.markdown("---")
        
        # Role-based navigation
        if st.session_state.user_role == "Student":
            page = st.radio(
                "📍 Navigate:",
                ["📅 My Schedule", "📊 My Results"],
                label_visibility="collapsed"
            )
        
        elif st.session_state.user_role == "Professor":
            page = st.radio(
                "📍 Navigate:",
                ["📅 My Schedule"],
                label_visibility="collapsed"
            )
        
        elif st.session_state.user_role == "Department Head":
            page = st.radio(
                "📍 Navigate:",
                ["🏢 Department Dashboard"],
                label_visibility="collapsed"
            )
        
        elif st.session_state.user_role == "Doyen":
            page = st.radio(
                "📍 Navigate:",
                ["🏛️ Doyen Dashboard"],
                label_visibility="collapsed"
            )
        
        else:  # Administrator
            page = st.radio(
                "📍 Navigate:",
                ["🏠 Dashboard", "📅 Manage Exams"],
                label_visibility="collapsed"
            )
        
        st.markdown("---")
        
        # System info
        st.caption("📊 **System Status**")
        total_exams = execute_query("SELECT COUNT(*) FROM examens", fetch=True)
        scheduled = execute_query("SELECT COUNT(*) FROM examens WHERE statut = 'programmé'", fetch=True)
        
        if total_exams and scheduled:
            progress = (scheduled[0][0] / total_exams[0][0] * 100) if total_exams[0][0] > 0 else 0
            st.progress(progress / 100)
            st.caption(f"{scheduled[0][0]}/{total_exams[0][0]} exams scheduled ({progress:.0f}%)")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.dept_id = None
            st.rerun()
        
        st.caption(f"🕐 {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
        
        return page  # THIS IS THE KEY FIX!

# ==========================================
# MAIN FUNCTION (FIXED!)
# ==========================================

def main():
    """Main application logic"""
    if not st.session_state.authenticated:
        login_page()
    else:
        # Get the selected page from sidebar
        page = show_sidebar()
        
        # Route to the correct page
        if page == "📅 My Schedule":
            if st.session_state.user_role == "Student":
                show_student_schedule()
            else:
                show_professor_schedule()
        
        elif page == "📊 My Results":
            show_student_results()
        
        elif page == "🏢 Department Dashboard":
            show_department_dashboard()
        
        elif page == "🏛️ Doyen Dashboard":
            show_doyen_dashboard()
        
        elif page == "🏠 Dashboard":
            show_admin_dashboard()
        
        elif page == "📅 Manage Exams":
            show_admin_exams()
        
        else:
            # Default fallback
            show_admin_dashboard()

if __name__ == "__main__":
    main()