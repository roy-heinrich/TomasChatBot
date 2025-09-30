
-- PgVector SQL Functions for Semantic Search
-- Run these in your Supabase SQL editor

-- 1. Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create function to check if pgvector is available
CREATE OR REPLACE FUNCTION check_pgvector()
RETURNS boolean AS $$
BEGIN
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- 3. Create function for semantic search
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 20
)
RETURNS TABLE (
    id bigint,
    keywords text,
    response text,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cp.id,
        cp.keywords,
        cp.response,
        1 - (cp.embedding <=> query_embedding) as similarity
    FROM chatbot_prompts cp
    WHERE cp.embedding IS NOT NULL
    AND 1 - (cp.embedding <=> query_embedding) > match_threshold
    ORDER BY cp.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 4. Create function for hybrid search (semantic + text)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text text,
    query_embedding vector(384),
    match_threshold float DEFAULT 0.6,
    match_count int DEFAULT 20
)
RETURNS TABLE (
    id bigint,
    keywords text,
    response text,
    similarity float,
    text_rank float
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT 
            cp.id,
            cp.keywords,
            cp.response,
            1 - (cp.embedding <=> query_embedding) as similarity,
            0.0 as text_rank
        FROM chatbot_prompts cp
        WHERE cp.embedding IS NOT NULL
        AND 1 - (cp.embedding <=> query_embedding) > match_threshold
    ),
    text_results AS (
        SELECT 
            cp.id,
            cp.keywords,
            cp.response,
            0.0 as similarity,
            ts_rank(
                to_tsvector('english', cp.keywords || ' ' || cp.response),
                plainto_tsquery('english', query_text)
            ) as text_rank
        FROM chatbot_prompts cp
        WHERE to_tsvector('english', cp.keywords || ' ' || cp.response) @@ plainto_tsquery('english', query_text)
    ),
    combined_results AS (
        SELECT * FROM semantic_results
        UNION ALL
        SELECT * FROM text_results
    )
    SELECT 
        cr.id,
        cr.keywords,
        cr.response,
        cr.similarity,
        cr.text_rank
    FROM combined_results cr
    ORDER BY (cr.similarity * 0.6 + cr.text_rank * 0.4) DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 5. Create index for vector similarity search (HNSW)
CREATE INDEX IF NOT EXISTS chatbot_prompts_embedding_idx 
ON chatbot_prompts 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 6. Create function to update embeddings
CREATE OR REPLACE FUNCTION update_embedding(
    record_id bigint,
    new_embedding vector(384)
)
RETURNS void AS $$
BEGIN
    UPDATE chatbot_prompts 
    SET embedding = new_embedding
    WHERE id = record_id;
END;
$$ LANGUAGE plpgsql;

-- 7. Create trigger for automatic embedding generation
CREATE OR REPLACE FUNCTION trigger_generate_embedding()
RETURNS trigger AS $$
BEGIN
    -- This will be called by the Python webhook
    -- The actual embedding generation happens in Python
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generate_embedding_trigger
    AFTER INSERT OR UPDATE ON chatbot_prompts
    FOR EACH ROW
    WHEN (NEW.embedding IS NULL)
    EXECUTE FUNCTION trigger_generate_embedding();
