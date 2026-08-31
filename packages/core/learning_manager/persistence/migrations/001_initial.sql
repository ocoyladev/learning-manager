-- Initial PostgreSQL schema for the persistence adapter.
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',
    preferred_language VARCHAR(20) NOT NULL DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS learning_goals (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    purpose VARCHAR(2000) NOT NULL,
    deadline DATE NOT NULL,
    daily_minutes INTEGER NOT NULL CHECK (daily_minutes BETWEEN 5 AND 240),
    preferred_formats JSONB NOT NULL DEFAULT '[]'::jsonb,
    success_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS concepts (
    goal_id VARCHAR(255) NOT NULL REFERENCES learning_goals(id) ON DELETE CASCADE,
    id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    prerequisites JSONB NOT NULL DEFAULT '[]'::jsonb,
    importance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    estimated_minutes INTEGER NOT NULL DEFAULT 15,
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (goal_id, id)
);

CREATE TABLE IF NOT EXISTS learner_concept_states (
    goal_id VARCHAR(255) NOT NULL,
    concept_id VARCHAR(255) NOT NULL,
    mastery DOUBLE PRECISION NOT NULL CHECK (mastery BETWEEN 0 AND 1),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    state VARCHAR(30) NOT NULL,
    last_seen DATE,
    last_assessed DATE,
    next_review DATE,
    misconceptions JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    PRIMARY KEY (goal_id, concept_id),
    FOREIGN KEY (goal_id, concept_id) REFERENCES concepts(goal_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessment_attempts (
    id VARCHAR(255) PRIMARY KEY,
    goal_id VARCHAR(255) NOT NULL,
    concept_id VARCHAR(255) NOT NULL,
    questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    answers JSONB NOT NULL DEFAULT '[]'::jsonb,
    score DOUBLE PRECISION NOT NULL CHECK (score BETWEEN 0 AND 1),
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (goal_id, concept_id) REFERENCES concepts(goal_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(255) PRIMARY KEY,
    goal_id VARCHAR(255) NOT NULL REFERENCES learning_goals(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    planned_minutes INTEGER NOT NULL,
    blocks JSONB NOT NULL DEFAULT '[]'::jsonb,
    rationale VARCHAR(4000) NOT NULL,
    reviews_included JSONB NOT NULL DEFAULT '[]'::jsonb,
    deferred_concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
    deadline_status VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(255) PRIMARY KEY,
    url VARCHAR(4000) NOT NULL,
    title VARCHAR(1000) NOT NULL,
    authority VARCHAR(30) NOT NULL,
    version VARCHAR(255),
    published_at DATE,
    retrieved_at DATE NOT NULL,
    content_path VARCHAR(2000)
);
