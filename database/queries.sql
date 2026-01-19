-- Detect conflicts (already in create_tables.sql, but add more)
-- KPI: Occupation rate
SELECT d.nom, AVG(g.capacite / l.capacite * 100) AS taux_occupation
FROM departements d
JOIN specializations s ON d.id = s.dept_id
JOIN formations f ON s.id = f.spec_id
JOIN groups g ON f.id = g.formation_id
JOIN examens e ON g.id = e.group_id
JOIN lieu_examen l ON e.salle_id = l.id
GROUP BY d.nom;

-- Prof hours
SELECT p.nom, SUM(e.duree_minutes)/60 AS heures_total
FROM professeurs p
JOIN examens e ON p.id = e.prof_id
GROUP BY p.nom
ORDER BY heures_total DESC;