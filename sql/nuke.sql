-- Drop triggers first
DROP TRIGGER IF EXISTS trigger_task_status_update ON celery_tasks;

-- Drop functions
DROP FUNCTION IF EXISTS update_task_status();

-- Drop indexes
DROP INDEX IF EXISTS idx_raw_jobs_created;
DROP INDEX IF EXISTS idx_processed_jobs_created;
DROP INDEX IF EXISTS idx_task_logs_task;
DROP INDEX IF EXISTS idx_processed_jobs_embedding;
DROP INDEX IF EXISTS idx_processed_jobs_task;
DROP INDEX IF EXISTS idx_raw_jobs_source;
DROP INDEX IF EXISTS idx_raw_jobs_task_id;
DROP INDEX IF EXISTS idx_celery_tasks_status;
DROP INDEX IF EXISTS idx_celery_tasks_task_id;

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS task_logs;
DROP TABLE IF EXISTS processed_jobs;
DROP TABLE IF EXISTS raw_jobs;
DROP TABLE IF EXISTS celery_tasks;
