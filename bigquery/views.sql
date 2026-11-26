-- Append-only table -> keep only the latest version of each (exam, student, subject)
CREATE OR REPLACE VIEW exam_analytics.v_latest_results AS
SELECT * EXCEPT (rn) FROM (
  SELECT r.*,
         ROW_NUMBER() OVER (PARTITION BY exam_id, student_id, subject_code
                            ORDER BY processed_at DESC) AS rn
  FROM exam_analytics.exam_results r
)
WHERE rn = 1;

-- 1. Subject-wise performance
CREATE OR REPLACE VIEW exam_analytics.v_subject_performance AS
SELECT exam_id, subject_code, subject_name,
  COUNT(*) AS students,
  ROUND(AVG(marks), 2) AS avg_marks,
  ROUND(AVG(percentage), 2) AS avg_percentage,
  MAX(marks) AS highest,
  MIN(marks) AS lowest,
  COUNTIF(result_status = 'PASS') AS passed,
  ROUND(100 * COUNTIF(result_status = 'PASS') / COUNT(*), 2) AS pass_percentage
FROM exam_analytics.v_latest_results
GROUP BY exam_id, subject_code, subject_name;

-- 2. One row per student
CREATE OR REPLACE VIEW exam_analytics.v_student_summary AS
SELECT exam_id, class_id, student_id,
  COUNT(*) AS subjects_taken,
  ROUND(AVG(percentage), 2) AS avg_percentage,
  COUNTIF(result_status = 'FAIL') AS subjects_failed,
  MIN(percentage) AS lowest_percentage
FROM exam_analytics.v_latest_results
GROUP BY exam_id, class_id, student_id;

-- 3. Class averages and overall pass percentage
CREATE OR REPLACE VIEW exam_analytics.v_class_summary AS
SELECT exam_id, class_id,
  COUNT(*) AS students,
  ROUND(AVG(avg_percentage), 2) AS class_avg_percentage,
  COUNTIF(subjects_failed = 0) AS passed_all,
  ROUND(100 * COUNTIF(subjects_failed = 0) / COUNT(*), 2) AS overall_pass_percentage,
  COUNTIF(subjects_failed > 0 OR avg_percentage < 50) AS needing_support
FROM exam_analytics.v_student_summary
GROUP BY exam_id, class_id;

-- 4. Students requiring additional support
CREATE OR REPLACE VIEW exam_analytics.v_students_needing_support AS
SELECT *,
  CASE
    WHEN subjects_failed > 0 AND avg_percentage < 50 THEN 'Failed subject(s) + low average'
    WHEN subjects_failed > 0 THEN 'Failed subject(s)'
    ELSE 'Low average (below 50%)'
  END AS reason
FROM exam_analytics.v_student_summary
WHERE subjects_failed > 0 OR avg_percentage < 50;

-- 5. Grade distribution
CREATE OR REPLACE VIEW exam_analytics.v_grade_distribution AS
SELECT exam_id, subject_code, subject_name, grade, COUNT(*) AS students
FROM exam_analytics.v_latest_results
GROUP BY exam_id, subject_code, subject_name, grade;
