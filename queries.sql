-- ============================================================================
-- Total number of rows in the table
-- ============================================================================
SELECT 
    COUNT(*) AS total_rows
FROM records;

-- ============================================================================
-- Top 5 categories by company count
-- ============================================================================
SELECT 
    company.category, 
    COUNT(DISTINCT company.name) AS company_count
FROM records as company
GROUP BY category
ORDER BY company_count DESC
LIMIT 5;

-- ============================================================================
-- Average rating by city (min 10 reviews)
-- ============================================================================
SELECT 
    company.city, 
    ROUND(AVG(REPLACE(NULLIF(company.rating, ''), ',', '.')::numeric), 2) AS companies_avg_rating,
    COUNT(company.name) AS companies_in_sample
FROM records AS company
WHERE company.reviews_count ~ '^-?\d+(\.\d+)?$'
  AND company.reviews_count::numeric >= 10
GROUP BY company.city
ORDER BY companies_avg_rating DESC;

-- ============================================================================
-- Website adoption rate by category (%)
-- ============================================================================
SELECT 
    COALESCE(company.category, 'Not specified') AS category,
    COUNT(*) AS total_companies,
    ROUND(
        (SUM(CASE WHEN company.site LIKE 'http%' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0)) * 100, 
        2
    ) AS website_share_pct
FROM records AS company
GROUP BY company.category
ORDER BY website_share_pct DESC;
