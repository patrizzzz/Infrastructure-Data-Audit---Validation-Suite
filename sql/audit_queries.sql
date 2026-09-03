-- ====================================================================
-- Infrastructure Data Audit & Validation Suite - SQL Analytics Queries
-- ====================================================================

-- 1. Regional Bridge Inventory & Condition Breakdown
SELECT 
    REGION,
    COUNT(BRIDGE_ID) AS Total_Bridges,
    SUM(CASE WHEN CONDITION = 'Good' THEN 1 ELSE 0 END) AS Good_Condition_Bridges,
    SUM(CASE WHEN CONDITION = 'Fair' THEN 1 ELSE 0 END) AS Fair_Condition_Bridges,
    SUM(CASE WHEN CONDITION = 'Poor' THEN 1 ELSE 0 END) AS Poor_Condition_Bridges,
    SUM(CASE WHEN CONDITION = 'Bad' THEN 1 ELSE 0 END) AS Bad_Condition_Bridges,
    ROUND(AVG(BR_LENGTH), 2) AS Avg_Bridge_Length_Meters,
    ROUND(SUM(BR_LENGTH) / 1000.0, 2) AS Total_Bridge_Span_KM
FROM clean_bridges
GROUP BY REGION
ORDER BY Total_Bridges DESC;


-- 2. High-Risk / Poor Condition Bridge Prioritization Audit
SELECT 
    BRIDGE_ID,
    BR_NAME,
    REGION,
    PROVINCE,
    DEO,
    ROAD_NAME,
    CONDITION,
    BR_LENGTH,
    ACTUAL_YR,
    COMMENTS
FROM clean_bridges
WHERE CONDITION IN ('Poor', 'Bad')
ORDER BY BR_LENGTH DESC;


-- 3. Top Data Quality Failure Modes by Issue Severity
SELECT 
    severity,
    issue_code,
    column,
    COUNT(*) AS issue_occurrence_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM validation_issues), 2) AS percentage_of_total_issues
FROM validation_issues
GROUP BY severity, issue_code, column
ORDER BY issue_occurrence_count DESC;


-- 4. District Engineering Office (DEO) Quality Risk Summary
SELECT 
    c.DEO,
    c.REGION,
    COUNT(DISTINCT c.BRIDGE_ID) AS Clean_Bridges_Count,
    COALESCE(vi.Total_Issues, 0) AS Flagged_Issues_Count,
    ROUND(COALESCE(vi.Total_Issues, 0) * 1.0 / COUNT(DISTINCT c.BRIDGE_ID), 2) AS Issue_Ratio_Per_Bridge
FROM clean_bridges c
LEFT JOIN (
    SELECT bridge_id, COUNT(*) as Total_Issues
    FROM validation_issues
    GROUP BY bridge_id
) vi ON c.BRIDGE_ID = vi.bridge_id
GROUP BY c.DEO, c.REGION
ORDER BY Flagged_Issues_Count DESC
LIMIT 15;


-- 5. Window Function: Bridge Length Ranking per Region
SELECT 
    BRIDGE_ID,
    BR_NAME,
    REGION,
    BR_LENGTH,
    RANK() OVER (PARTITION BY REGION ORDER BY BR_LENGTH DESC) as Region_Length_Rank,
    ROUND(AVG(BR_LENGTH) OVER (PARTITION BY REGION), 2) as Regional_Avg_Length
FROM clean_bridges
WHERE BR_LENGTH IS NOT NULL
LIMIT 20;
