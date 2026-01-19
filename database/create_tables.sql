

-- Drop the old function with wrong signature
DROP FUNCTION IF EXISTS get_exam_statistics();


-- Drop existing tables (in correct order)
DROP TABLE IF EXISTS surveillances CASCADE;
DROP TABLE IF EXISTS conflits CASCADE;
DROP TABLE IF EXISTS examens CASCADE;
DROP TABLE IF EXISTS inscriptions CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS professeurs CASCADE;
DROP TABLE IF EXISTS etudiants CASCADE;
DROP TABLE IF EXISTS lieu_examen CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS formations CASCADE;
DROP TABLE IF EXISTS specializations CASCADE;
DROP TABLE IF EXISTS departements CASCADE;
DROP TABLE IF EXISTS salles CASCADE;  -- Remove this old table too

-- Drop old functions
DROP FUNCTION IF EXISTS get_exam_statistics();
DROP FUNCTION IF EXISTS detecter_conflits();
DROP FUNCTION IF EXISTS get_table_stats();

-- ============================================
-- CORE TABLES
-- ============================================

CREATE TABLE departements (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE specializations (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    dept_id INTEGER NOT NULL REFERENCES departements(id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE formations (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    spec_id INTEGER NOT NULL REFERENCES specializations(id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE,
    nb_modules INTEGER DEFAULT 6 CHECK (nb_modules > 0),
    niveau VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    formation_id INTEGER NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    capacite INTEGER NOT NULL CHECK (capacite > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_group_per_formation UNIQUE(nom, formation_id)
);

CREATE TABLE etudiants (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    matricule VARCHAR(20) UNIQUE NOT NULL,
    group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    promo INTEGER CHECK (promo >= 2000),
    email VARCHAR(150) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE professeurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100),
    dept_id INTEGER REFERENCES departements(id) ON DELETE SET NULL,
    specialite VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    nb_surveillances INTEGER DEFAULT 0 CHECK (nb_surveillances >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lieu_examen (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    capacite INTEGER NOT NULL CHECK (capacite > 0),
    type VARCHAR(50),
    batiment VARCHAR(100),
    equipements TEXT,
    disponible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    credits INTEGER DEFAULT 3 CHECK (credits > 0),
    spec_id INTEGER NOT NULL REFERENCES specializations(id) ON DELETE CASCADE,
    semestre INTEGER CHECK (semestre IN (1, 2)),
    pre_req_id INTEGER REFERENCES modules(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inscriptions (
    id SERIAL PRIMARY KEY,
    etudiant_id INTEGER NOT NULL REFERENCES etudiants(id) ON DELETE CASCADE,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    annee_academique VARCHAR(10),
    note DECIMAL(4,2) CHECK (note IS NULL OR (note >= 0 AND note <= 20)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_inscription UNIQUE(etudiant_id, module_id, annee_academique)
);

CREATE TABLE examens (
    id SERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    prof_id INTEGER REFERENCES professeurs(id) ON DELETE SET NULL,
    salle_id INTEGER REFERENCES lieu_examen(id) ON DELETE SET NULL,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    date_heure TIMESTAMP,
    duree_minutes INTEGER DEFAULT 90 CHECK (duree_minutes > 0),
    type_examen VARCHAR(50) DEFAULT 'Midterm',
    priorite_dept BOOLEAN DEFAULT TRUE,
    statut VARCHAR(20) DEFAULT 'planifié' CHECK (statut IN ('planifié', 'programmé', 'en_cours', 'terminé', 'annulé')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conflits (
    id SERIAL PRIMARY KEY,
    examen_id INTEGER NOT NULL REFERENCES examens(id) ON DELETE CASCADE,
    type_conflit VARCHAR(100) NOT NULL,
    description TEXT,
    severite VARCHAR(20) DEFAULT 'moyen' CHECK (severite IN ('faible', 'moyen', 'critique')),
    resolu BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE surveillances (
    id SERIAL PRIMARY KEY,
    prof_id INTEGER NOT NULL REFERENCES professeurs(id) ON DELETE CASCADE,
    examen_id INTEGER NOT NULL REFERENCES examens(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'surveillant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_surveillance UNIQUE(prof_id, examen_id)
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_etudiants_group ON etudiants(group_id);
CREATE INDEX idx_etudiants_matricule ON etudiants(matricule);
CREATE INDEX idx_groups_formation ON groups(formation_id);
CREATE INDEX idx_formations_spec ON formations(spec_id);
CREATE INDEX idx_specializations_dept ON specializations(dept_id);
CREATE INDEX idx_modules_spec ON modules(spec_id);
CREATE INDEX idx_modules_code ON modules(code);
CREATE INDEX idx_inscriptions_etudiant ON inscriptions(etudiant_id);
CREATE INDEX idx_inscriptions_module ON inscriptions(module_id);
CREATE INDEX idx_examens_date ON examens(date_heure);
CREATE INDEX idx_examens_module ON examens(module_id);
CREATE INDEX idx_examens_salle ON examens(salle_id);
CREATE INDEX idx_examens_group ON examens(group_id);
CREATE INDEX idx_examens_statut ON examens(statut);
CREATE INDEX idx_surveillances_prof ON surveillances(prof_id);
CREATE INDEX idx_surveillances_exam ON surveillances(examen_id);
CREATE INDEX idx_conflits_exam ON conflits(examen_id);
CREATE INDEX idx_conflits_resolu ON conflits(resolu);
CREATE INDEX idx_professeurs_dept ON professeurs(dept_id);
CREATE INDEX idx_professeurs_email ON professeurs(email);

-- ============================================
-- FUNCTIONS (NEW SIGNATURES)
-- ============================================

-- Function: Detect conflicts
CREATE OR REPLACE FUNCTION detecter_conflits()
RETURNS TABLE(
    conflict_type VARCHAR,
    conflict_count BIGINT,
    description TEXT
) AS $$
BEGIN
    DELETE FROM conflits WHERE resolu = FALSE;
    
    INSERT INTO conflits (examen_id, type_conflit, description, severite)
    SELECT DISTINCT e1.id, 
           'Conflit étudiant', 
           'Étudiant a plusieurs examens le même jour',
           'critique'
    FROM examens e1
    JOIN examens e2 ON e1.id < e2.id
    JOIN inscriptions i1 ON e1.module_id = i1.module_id
    JOIN inscriptions i2 ON e2.module_id = i2.module_id 
    WHERE i1.etudiant_id = i2.etudiant_id
      AND DATE(e1.date_heure) = DATE(e2.date_heure)
      AND e1.group_id = e2.group_id
      AND e1.date_heure IS NOT NULL
      AND e2.date_heure IS NOT NULL;
    
    INSERT INTO conflits (examen_id, type_conflit, description, severite)
    SELECT e.id,
           'Conflit professeur',
           'Professeur a plus de 3 examens par jour',
           'moyen'
    FROM examens e
    WHERE e.prof_id IN (
        SELECT prof_id
        FROM examens
        WHERE date_heure IS NOT NULL
        GROUP BY prof_id, DATE(date_heure)
        HAVING COUNT(*) > 3
    ) AND e.date_heure IS NOT NULL;
    
    INSERT INTO conflits (examen_id, type_conflit, description, severite)
    SELECT e.id,
           'Conflit capacité salle',
           'Capacité de la salle dépassée',
           'critique'
    FROM examens e
    JOIN lieu_examen l ON e.salle_id = l.id
    JOIN groups g ON e.group_id = g.id
    WHERE g.capacite > l.capacite
      AND e.salle_id IS NOT NULL;
    
    INSERT INTO conflits (examen_id, type_conflit, description, severite)
    SELECT DISTINCT e1.id,
           'Conflit horaire salle',
           'Salle occupée par un autre examen',
           'critique'
    FROM examens e1
    JOIN examens e2 ON e1.id < e2.id AND e1.salle_id = e2.salle_id
    WHERE e1.date_heure < (e2.date_heure + INTERVAL '1 minute' * e2.duree_minutes)
      AND e2.date_heure < (e1.date_heure + INTERVAL '1 minute' * e1.duree_minutes)
      AND e1.date_heure IS NOT NULL
      AND e2.date_heure IS NOT NULL;
    
    RETURN QUERY
    SELECT type_conflit, COUNT(*), 'Conflits détectés'::TEXT
    FROM conflits
    WHERE resolu = FALSE
    GROUP BY type_conflit;
END;
$$ LANGUAGE plpgsql;

-- Function: Get exam statistics (FIXED SIGNATURE)
CREATE OR REPLACE FUNCTION get_exam_statistics()
RETURNS TABLE(
    total_exams BIGINT,
    scheduled_exams BIGINT,
    total_conflicts BIGINT,
    avg_room_occupation NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT e.id)::BIGINT as total_exams,
        COUNT(DISTINCT CASE WHEN e.statut = 'programmé' THEN e.id END)::BIGINT as scheduled_exams,
        COUNT(DISTINCT c.id)::BIGINT as total_conflicts,
        COALESCE(
            ROUND(
                AVG(g.capacite::NUMERIC / NULLIF(l.capacite, 0) * 100) 
                FILTER (WHERE l.capacite > 0), 
                2
            ), 
            0
        )::NUMERIC as avg_room_occupation
    FROM examens e
    LEFT JOIN conflits c ON e.id = c.examen_id AND c.resolu = FALSE
    LEFT JOIN lieu_examen l ON e.salle_id = l.id
    LEFT JOIN groups g ON e.group_id = g.id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get table statistics
CREATE OR REPLACE FUNCTION get_table_stats()
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT
) AS $$
DECLARE
    r RECORD;
    count_result BIGINT;
BEGIN
    FOR r IN 
        SELECT t.table_name::TEXT as tname
        FROM information_schema.tables t
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', r.tname) INTO count_result;
        table_name := r.tname;
        row_count := count_result;
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ DATABASE SCHEMA CREATED SUCCESSFULLY';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Tables: 12';
    RAISE NOTICE 'Functions fixed and recreated';
    RAISE NOTICE 'Ready for data generation!';
    RAISE NOTICE '============================================';
END $$;