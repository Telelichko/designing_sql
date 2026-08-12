-- ============================================================================
-- Total number of rows in the table
-- ============================================================================
SELECT 
    COUNT(*) AS total_rows
FROM companies;

-- ============================================================================
-- Top 5 categories by companies count
-- ============================================================================
SELECT 
    companies.category, 
    COUNT(DISTINCT companies.name) AS company_count
FROM companies
GROUP BY category
ORDER BY company_count DESC
LIMIT 5;

-- ============================================================================
-- Average rating by city (min 10 reviews)
-- ============================================================================
SELECT 
    companies.city, 
    ROUND(AVG(REPLACE(NULLIF(companies.rating, ''), ',', '.')::numeric), 2) AS companies_avg_rating,
    COUNT(companies.name) AS companies_in_sample
FROM companies
WHERE companies.reviews_count ~ '^-?\d+(\.\d+)?$'
  AND companies.reviews_count::numeric >= 10
GROUP BY companies.city
ORDER BY companies_avg_rating DESC;

-- ============================================================================
-- Website adoption rate by category (%)
-- ============================================================================
SELECT 
    COALESCE(companies.category, 'Not specified') AS category,
    COUNT(*) AS total_companies,
    ROUND(
        (SUM(CASE WHEN companies.site LIKE 'http%' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0)) * 100, 
        2
    ) AS website_share_pct
FROM companies
GROUP BY companies.category
ORDER BY website_share_pct DESC;
