-- ============================================================================
-- Total number of rows in the table (all records)
-- ============================================================================
SELECT 
    COUNT(*) AS total_rows
FROM companies;


-- ============================================================================
-- Total number of unique companies (by primary key id)
-- ============================================================================
SELECT 
    COUNT(DISTINCT id) AS unique_by_id
FROM companies;


-- ============================================================================
-- Total number of unique company names
-- (to check if some names are repeated with different IDs)
-- ============================================================================
SELECT 
    COUNT(DISTINCT name) AS unique_by_name
FROM companies;


-- ============================================================================
-- Difference between total rows and unique IDs (should be 0 after dedup)
-- ============================================================================
SELECT 
    COUNT(*) AS total,
    COUNT(DISTINCT id) AS unique_ids,
    COUNT(*) - COUNT(DISTINCT id) AS duplicates_removed
FROM companies;


-- ============================================================================
-- Duplicates by company name only (showing count and IDs)
-- ============================================================================
SELECT 
    name,
    COUNT(*) AS duplicate_count,
    STRING_AGG(id, ', ') AS duplicate_ids
FROM companies
GROUP BY name
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, name;


-- ============================================================================
-- Duplicates by company name AND city (more specific)
-- ============================================================================
SELECT 
    name,
    city,
    COUNT(*) AS duplicate_count,
    STRING_AGG(id, ', ') AS duplicate_ids
FROM companies
GROUP BY name, city
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, name, city;


-- ============================================================================
-- Full duplicate rows (all data columns except id)
-- Shows exact duplicates across all business columns
-- ============================================================================
SELECT 
    name, category, city, address, rating, reviews_count, site, phone, email,
    COUNT(*) AS duplicate_count,
    STRING_AGG(id, ', ') AS duplicate_ids
FROM companies
GROUP BY name, category, city, address, rating, reviews_count, site, phone, email
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;


-- ============================================================================
-- List all rows that are duplicates by full row (for manual inspection)
-- ============================================================================
SELECT *
FROM companies
WHERE (name, category, city, address, rating, reviews_count, site, phone, email) IN (
    SELECT name, category, city, address, rating, reviews_count, site, phone, email
    FROM companies
    GROUP BY name, category, city, address, rating, reviews_count, site, phone, email
    HAVING COUNT(*) > 1
)
ORDER BY name, id;


-- ============================================================================
-- Check for rows with invalid email (should be 0 after validation)
-- ============================================================================
SELECT 
    COUNT(*) AS invalid_email_count
FROM companies
WHERE email IS NULL 
   OR email NOT LIKE '%@%.%';