# Looker Studio dashboard setup

1. Looker Studio -> Create -> Report -> BigQuery connector -> project / dataset `exam_analytics`.
2. Add these views as data sources: `v_subject_performance`, `v_class_summary`,
   `v_students_needing_support`, `v_grade_distribution`, `v_student_summary`.
3. Page layout
   - Scorecards: students, overall average, students passed all subjects, students needing support
   - Bar chart: `avg_percentage` by `subject_name`  (v_subject_performance)
   - Bar chart: `pass_percentage` by `subject_name`
   - Bar chart: `class_avg_percentage` by `class_id`  (v_class_summary)
   - Stacked bar: `students` by `grade`               (v_grade_distribution)
   - Table: `student_id, class_id, avg_percentage, subjects_failed, reason` (v_students_needing_support),
     with conditional formatting on `subjects_failed`
4. Add drop-down controls for `exam_id` and `class_id`.
5. Data source settings -> Data freshness -> shorten it (default for BigQuery is 12 hours) so new results appear quickly.
