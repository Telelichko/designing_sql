-- ============================================================================
-- Clean database: drop all tables in public schema (cascade)
-- ============================================================================
DO $$ 
DECLARE
    r RECORD;
BEGIN
    -- Loop through all tables in the public schema
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;

-- ============================================================================
-- Alternative: completely reset schema (drop and recreate)
-- ============================================================================
-- USE WITH CAUTION – this removes all objects including sequences and types
-- 
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;
-- GRANT ALL ON SCHEMA public TO myuser;