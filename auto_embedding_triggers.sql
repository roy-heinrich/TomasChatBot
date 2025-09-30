-- Auto Embedding Generation Triggers
-- Run these in your Supabase SQL editor

-- 1. Create function to generate embeddings (calls webhook)
CREATE OR REPLACE FUNCTION generate_embedding_for_record()
RETURNS trigger AS $$
DECLARE
    webhook_url text;
    payload jsonb;
    response text;
BEGIN
    -- Get webhook URL from environment or use default
    webhook_url := current_setting('app.embedding_webhook_url', true);
    
    -- If no webhook URL is set, skip embedding generation
    IF webhook_url IS NULL OR webhook_url = '' THEN
        RAISE NOTICE 'No webhook URL configured, skipping embedding generation';
        RETURN NEW;
    END IF;
    
    -- Prepare payload for webhook
    payload := jsonb_build_object(
        'type', 'INSERT',
        'record', jsonb_build_object(
            'id', NEW.id,
            'keywords', COALESCE(NEW.keywords, ''),
            'response', COALESCE(NEW.response, '')
        )
    );
    
    -- Call webhook (this would need to be implemented with http extension)
    -- For now, we'll just log the action
    RAISE NOTICE 'Would call webhook for record % with payload %', NEW.id, payload;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Create trigger for INSERT operations
CREATE TRIGGER trigger_generate_embedding_insert
    AFTER INSERT ON chatbot_prompts
    FOR EACH ROW
    WHEN (NEW.keywords IS NOT NULL OR NEW.response IS NOT NULL)
    EXECUTE FUNCTION generate_embedding_for_record();

-- 3. Create trigger for UPDATE operations (when keywords or response change)
CREATE TRIGGER trigger_generate_embedding_update
    AFTER UPDATE ON chatbot_prompts
    FOR EACH ROW
    WHEN (
        (OLD.keywords IS DISTINCT FROM NEW.keywords) OR 
        (OLD.response IS DISTINCT FROM NEW.response)
    )
    EXECUTE FUNCTION generate_embedding_for_record();

-- 4. Create function to manually generate embeddings for existing records
CREATE OR REPLACE FUNCTION generate_missing_embeddings()
RETURNS TABLE (
    processed_count integer,
    total_count integer
) AS $$
DECLARE
    record_count integer;
    processed_count integer := 0;
    rec RECORD;
BEGIN
    -- Count records without embeddings
    SELECT COUNT(*) INTO record_count
    FROM chatbot_prompts 
    WHERE embedding IS NULL;
    
    -- Process each record without embedding
    FOR rec IN 
        SELECT id, keywords, response 
        FROM chatbot_prompts 
        WHERE embedding IS NULL
    LOOP
        -- This would call the embedding generation
        -- For now, we'll just mark as processed
        processed_count := processed_count + 1;
        
        RAISE NOTICE 'Processing record % for embedding generation', rec.id;
    END LOOP;
    
    RETURN QUERY SELECT processed_count, record_count;
END;
$$ LANGUAGE plpgsql;

-- 5. Create function to check embedding status
CREATE OR REPLACE FUNCTION check_embedding_status()
RETURNS TABLE (
    total_records integer,
    records_with_embeddings integer,
    records_without_embeddings integer,
    embedding_percentage numeric
) AS $$
DECLARE
    total_count integer;
    with_embeddings integer;
    without_embeddings integer;
    percentage numeric;
BEGIN
    -- Count total records
    SELECT COUNT(*) INTO total_count FROM chatbot_prompts;
    
    -- Count records with embeddings
    SELECT COUNT(*) INTO with_embeddings 
    FROM chatbot_prompts 
    WHERE embedding IS NOT NULL;
    
    -- Count records without embeddings
    SELECT COUNT(*) INTO without_embeddings 
    FROM chatbot_prompts 
    WHERE embedding IS NULL;
    
    -- Calculate percentage
    IF total_count > 0 THEN
        percentage := (with_embeddings::numeric / total_count::numeric) * 100;
    ELSE
        percentage := 0;
    END IF;
    
    RETURN QUERY SELECT total_count, with_embeddings, without_embeddings, percentage;
END;
$$ LANGUAGE plpgsql;

-- 6. Create function to clean up old embeddings (optional)
CREATE OR REPLACE FUNCTION cleanup_embeddings()
RETURNS integer AS $$
DECLARE
    cleaned_count integer := 0;
BEGIN
    -- Remove embeddings from records with empty or null keywords and response
    UPDATE chatbot_prompts 
    SET embedding = NULL 
    WHERE (keywords IS NULL OR keywords = '') 
    AND (response IS NULL OR response = '')
    AND embedding IS NOT NULL;
    
    GET DIAGNOSTICS cleaned_count = ROW_COUNT;
    
    RETURN cleaned_count;
END;
$$ LANGUAGE plpgsql;

-- 7. Grant necessary permissions
GRANT EXECUTE ON FUNCTION generate_embedding_for_record() TO authenticated;
GRANT EXECUTE ON FUNCTION generate_missing_embeddings() TO authenticated;
GRANT EXECUTE ON FUNCTION check_embedding_status() TO authenticated;
GRANT EXECUTE ON FUNCTION cleanup_embeddings() TO authenticated;
