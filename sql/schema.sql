-- Core tables
CREATE TYPE difficulty_level AS ENUM ('EASY', 'MEDIUM', 'HARD');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game sessions with enhanced tracking
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_time_seconds INTEGER,
    total_score INTEGER DEFAULT 0,
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    avg_drawing_time_ms INTEGER DEFAULT 0,
    streak_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drawing attempts with detailed metrics
CREATE TABLE IF NOT EXISTS drawing_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id INTEGER REFERENCES game_sessions(id) ON DELETE CASCADE,
    word_prompt VARCHAR(100) NOT NULL,
    difficulty difficulty_level NOT NULL,
    is_correct BOOLEAN NOT NULL,
    drawing_time_ms INTEGER NOT NULL,
    recognition_accuracy FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User performance metrics (aggregated stats)
CREATE TABLE IF NOT EXISTS user_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    total_games_played INTEGER DEFAULT 0,
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    total_time_spent_seconds INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    best_score INTEGER DEFAULT 0,
    fastest_correct_ms INTEGER,
    highest_streak INTEGER DEFAULT 0,
    easy_accuracy FLOAT DEFAULT 0,
    medium_accuracy FLOAT DEFAULT 0,
    hard_accuracy FLOAT DEFAULT 0,
    avg_drawing_time_ms INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_attempts_user ON drawing_attempts(user_id);
CREATE INDEX idx_attempts_session ON drawing_attempts(session_id);
CREATE INDEX idx_sessions_user ON game_sessions(user_id);
CREATE INDEX idx_attempts_difficulty ON drawing_attempts(difficulty);
CREATE INDEX idx_attempts_created ON drawing_attempts(created_at);

-- Views for dashboard queries
CREATE OR REPLACE VIEW user_progress_view AS
SELECT 
    u.id as user_id,
    u.username,
    um.total_games_played,
    um.total_attempts,
    um.successful_attempts,
    ((um.successful_attempts::NUMERIC / NULLIF(um.total_attempts, 0) * 100))::NUMERIC(10,2) as overall_accuracy,
    um.avg_drawing_time_ms,
    um.current_level,
    um.best_score,
    um.highest_streak,
    um.easy_accuracy,
    um.medium_accuracy,
    um.hard_accuracy
FROM users u
LEFT JOIN user_metrics um ON u.id = um.user_id;

-- Weekly progress view
CREATE OR REPLACE VIEW weekly_progress_view AS
SELECT 
    user_id,
    DATE_TRUNC('week', created_at) as week_start,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as successful_attempts,
    (AVG(drawing_time_ms))::NUMERIC(10,2) as avg_drawing_time,
    ((SUM(CASE WHEN is_correct THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100))::NUMERIC(10,2) as accuracy
FROM drawing_attempts
GROUP BY user_id, DATE_TRUNC('week', created_at);

-- Trigger to update user metrics
CREATE OR REPLACE FUNCTION update_user_metrics()
RETURNS TRIGGER AS $$
DECLARE
    current_streak integer;
    max_streak integer;
    session_score integer;
    total_session_attempts integer;
BEGIN
    -- Calculate current streak using a simpler approach
    WITH consecutive_correct AS (
        SELECT 
            row_number() OVER (ORDER BY created_at) - 
            row_number() OVER (PARTITION BY is_correct ORDER BY created_at) as grp,
            is_correct
        FROM drawing_attempts
        WHERE session_id = NEW.session_id
        ORDER BY created_at
    )
    SELECT COALESCE(MAX(cnt), 0)
    INTO current_streak
    FROM (
        SELECT COUNT(*) as cnt
        FROM consecutive_correct
        WHERE is_correct = true
        GROUP BY grp
    ) as streak_counts;

    -- Get current session statistics
    SELECT 
        COUNT(*) FILTER (WHERE is_correct = true),
        COUNT(*)
    INTO session_score, total_session_attempts
    FROM drawing_attempts
    WHERE session_id = NEW.session_id;

    -- Update game session statistics
    UPDATE game_sessions
    SET 
        streak_count = current_streak,
        successful_attempts = session_score,
        total_score = session_score,  -- Update total_score based on successful attempts
        total_attempts = total_session_attempts  -- Update total_attempts
    WHERE id = NEW.session_id;

    -- Update user metrics
    INSERT INTO user_metrics (
        user_id,
        total_attempts,
        successful_attempts,
        avg_drawing_time_ms,
        fastest_correct_ms,
        highest_streak,
        best_score
    )
    VALUES (
        NEW.user_id,
        1,
        CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        NEW.drawing_time_ms,
        CASE WHEN NEW.is_correct THEN NEW.drawing_time_ms ELSE NULL END,
        current_streak,
        session_score
    )
    ON CONFLICT (user_id) DO UPDATE SET
        total_attempts = user_metrics.total_attempts + 1,
        successful_attempts = user_metrics.successful_attempts + 
            CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        avg_drawing_time_ms = (
            (user_metrics.avg_drawing_time_ms * user_metrics.total_attempts + NEW.drawing_time_ms) / 
            (user_metrics.total_attempts + 1)
        ),
        fastest_correct_ms = CASE 
            WHEN NEW.is_correct THEN
                LEAST(
                    COALESCE(user_metrics.fastest_correct_ms, NEW.drawing_time_ms),
                    NEW.drawing_time_ms
                )
            ELSE user_metrics.fastest_correct_ms
        END,
        highest_streak = GREATEST(user_metrics.highest_streak, current_streak),
        best_score = GREATEST(user_metrics.best_score, session_score),
        last_updated = CURRENT_TIMESTAMP;

    -- Update difficulty-specific accuracy
    IF NEW.is_correct THEN
        CASE NEW.difficulty
            WHEN 'EASY' THEN
                UPDATE user_metrics 
                SET easy_accuracy = (easy_accuracy + NEW.recognition_accuracy) / 2
                WHERE user_id = NEW.user_id;
            WHEN 'MEDIUM' THEN
                UPDATE user_metrics 
                SET medium_accuracy = (medium_accuracy + NEW.recognition_accuracy) / 2
                WHERE user_id = NEW.user_id;
            WHEN 'HARD' THEN
                UPDATE user_metrics 
                SET hard_accuracy = (hard_accuracy + NEW.recognition_accuracy) / 2
                WHERE user_id = NEW.user_id;
        END CASE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_user_metrics
AFTER INSERT ON drawing_attempts
FOR EACH ROW
EXECUTE FUNCTION update_user_metrics();


CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    blacklisted_on TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_token_blacklist_token ON token_blacklist(token);
