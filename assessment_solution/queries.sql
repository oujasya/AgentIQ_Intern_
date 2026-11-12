-- Q18. All three queries operate on validated, normalized, unique records.

-- 1. Open-record counts by source. Sources with no open work are omitted.
SELECT source, COUNT(*) AS open_count
FROM records
WHERE status = 'open'
GROUP BY source
ORDER BY source;

-- 2. The five records with the most owner changes, with stable tie-breaking.
SELECT source, id, owner_changes
FROM records
ORDER BY owner_changes DESC, source ASC, id ASC
LIMIT 5;

-- 3. Categories containing at least five records.
SELECT category, COUNT(*) AS record_count
FROM records
GROUP BY category
HAVING COUNT(*) >= 5
ORDER BY record_count DESC, category ASC;
