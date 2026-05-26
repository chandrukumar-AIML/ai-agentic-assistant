-- backend/memory/init.sql
-- Run once to set up pgvector for Mem0

CREATE EXTENSION IF NOT EXISTS vector;

-- Mem0 creates its own tables automatically.
-- This just ensures pgvector extension is available.

-- Optional: custom audit table for memory operations
CREATE TABLE IF NOT EXISTS memory_audit (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(255) NOT NULL,
    action      VARCHAR(50)  NOT NULL,  -- 'add', 'delete', 'search'
    memory_type VARCHAR(50),
    content     TEXT,
    session_id  VARCHAR(255),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_audit_user_id 
    ON memory_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_audit_created_at 
    ON memory_audit(created_at);