-- Celery task tracking table
CREATE TABLE celery_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,  -- Celery task UUID
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    task_name VARCHAR(255) NOT NULL,  -- e.g., 'scrape_jobs'
    task_args JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Store task arguments as JSONB
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retries INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE
);

-- Raw scraped jobs table (before processing)
CREATE TABLE raw_jobs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,  -- Changed to match task_id from celery_tasks
    external_id VARCHAR(255),
    raw_data JSONB NOT NULL,  -- Store complete raw job data
    source_site VARCHAR(50),  -- indeed, linkedin, etc.
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    job_url VARCHAR(512),
    job_type VARCHAR(100),
    salary_interval VARCHAR(20),
    salary_min DECIMAL(12,2),
    salary_max DECIMAL(12,2),
    salary_currency VARCHAR(3),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES celery_tasks(task_id)  -- Changed to reference task_id
);

-- Processed jobs table (after cleaning/normalization)
CREATE TABLE processed_jobs (
    id SERIAL PRIMARY KEY,
    raw_job_id INTEGER REFERENCES raw_jobs(id),
    task_id VARCHAR(255) NOT NULL,  -- Changed to match task_id from celery_tasks
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    url VARCHAR(512),  -- Changed from job_url to url to match ProcessedJob model
    job_type VARCHAR(100),
    salary_min DECIMAL(12,2),
    salary_max DECIMAL(12,2),
    salary_currency VARCHAR(3),
    pinecone_id VARCHAR(255),
    embedding_status VARCHAR(50) DEFAULT 'PENDING',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES celery_tasks(task_id)  -- Changed to reference task_id
);

-- Task processing logs
CREATE TABLE task_logs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES celery_tasks(id),
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_celery_tasks_task_id ON celery_tasks(task_id);
CREATE INDEX idx_celery_tasks_status ON celery_tasks(status);
CREATE INDEX idx_raw_jobs_task_id ON raw_jobs(task_id);
CREATE INDEX idx_raw_jobs_source ON raw_jobs(source_site);
CREATE INDEX idx_processed_jobs_task ON processed_jobs(task_id);
CREATE INDEX idx_processed_jobs_embedding ON processed_jobs(embedding_status);
CREATE INDEX idx_task_logs_task ON task_logs(task_id);
CREATE INDEX idx_processed_jobs_created ON processed_jobs(processed_at);
CREATE INDEX idx_raw_jobs_created ON raw_jobs(created_at);

-- Status update trigger
CREATE OR REPLACE FUNCTION update_task_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'PROCESSING' AND OLD.started_at IS NULL THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    ELSIF NEW.status IN ('SUCCESS', 'FAILURE') AND OLD.completed_at IS NULL THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_task_status_update
    BEFORE UPDATE ON celery_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_task_status();
