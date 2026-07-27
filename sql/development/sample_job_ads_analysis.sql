\set ON_ERROR_STOP on

BEGIN;

DROP TABLE IF EXISTS practice_job_ads;

CREATE TEMP TABLE practice_job_ads (
    job_id integer PRIMARY KEY,
    title text NOT NULL,
    employer text NOT NULL,
    city text,
    role_family text NOT NULL,
    working_language text NOT NULL,
    skills text[] NOT NULL,
    publication_date date NOT NULL,
    active_status boolean NOT NULL
);

INSERT INTO practice_job_ads (
    job_id,
    title,
    employer,
    city,
    role_family,
    working_language,
    skills,
    publication_date,
    active_status
)
VALUES
    (1, 'Junior Data Engineer', 'Nordic Data AS', 'Oslo', 'Data Engineering',
     'English', ARRAY['Python', 'SQL', 'Docker'], DATE '2026-07-01', true),
    (2, 'Analytics Engineer', 'Fjord Analytics', 'Bergen', 'Analytics',
     'English and Norwegian', ARRAY['SQL', 'dbt', 'Power BI'], DATE '2026-07-02', true),
    (3, 'Applied AI Developer', 'Arctic AI', 'Trondheim', 'Applied AI',
     'English', ARRAY['Python', 'FastAPI', 'RAG'], DATE '2026-07-03', true),
    (4, 'Data Platform Developer', 'Oslo Systems', 'Oslo', 'Data Engineering',
     'Norwegian', ARRAY['Python', 'PostgreSQL', 'Azure'], DATE '2026-07-04', true),
    (5, 'Computer Vision Engineer', 'Vision North', 'Stavanger', 'Computer Vision',
     'English', ARRAY['Python', 'PyTorch', 'Docker'], DATE '2026-07-05', false),
    (6, 'BI Developer', 'Insight Norge', 'Oslo', 'Analytics',
     'English and Norwegian', ARRAY['SQL', 'Power BI', 'Fabric'], DATE '2026-07-06', true),
    (7, 'Graduate Data Engineer', 'Green Pipeline', 'Ås', 'Data Engineering',
     'English', ARRAY['Python', 'SQL', 'PostgreSQL'], DATE '2026-07-07', true),
    (8, 'AI Application Developer', 'Copilot Labs', 'Oslo', 'Applied AI',
     'English', ARRAY['Python', 'FastAPI', 'Copilot Studio'], DATE '2026-07-08', true),
    (9, 'Senior Analytics Engineer', 'Metric Works', 'Bergen', 'Analytics',
     'Norwegian', ARRAY['SQL', 'dbt', 'Snowflake'], DATE '2026-07-09', true),
    (10, 'Junior ML Engineer', 'Northern Models', NULL, 'Applied AI',
     'English', ARRAY['Python', 'Docker', 'PostgreSQL'], DATE '2026-07-10', true);

\echo ''
\echo 'Synthetic job advertisement dataset initialized for baseline analysis.'
\echo ''

-- Analysis 1: Active advertisements by publication date
-- Return all active advertisements, newest first.

-- Write your query below:

SELECT *
FROM practice_job_ads
WHERE active_status IS TRUE
ORDER BY publication_date DESC;

-- Analysis 2: Active advertisement volume by role family
-- Count active advertisements by role_family.
-- Sort from the highest count to the lowest.

-- Write your query below:
SELECT role_family, COUNT(*) AS active_job_count
FROM practice_job_ads
WHERE active_status IS TRUE
GROUP BY role_family
ORDER BY active_job_count DESC;

-- Analysis 3: Active advertisements supporting English
-- Return active advertisements that can be worked in English.
-- Hint: the field may contain either "English" or "English and Norwegian".

-- Write your query below:
SELECT *
FROM practice_job_ads
WHERE active_status IS TRUE
  AND working_language LIKE '%English%'
ORDER BY publication_date DESC;

-- Analysis 4: Active advertisement volume by city
-- Count active advertisements by city.
-- Place missing cities in a visible "Unknown" category.

-- Write your query below:
SELECT
    COALESCE(city, 'Unknown') AS city,
    COUNT(*) AS active_job_count
FROM practice_job_ads
WHERE active_status IS TRUE
GROUP BY COALESCE(city, 'Unknown')
ORDER BY active_job_count DESC, city ASC;


-- Analysis 5: Early-career advertisement identification
-- Return advertisements whose title suggests a junior, graduate, or early-career role.
-- Make the title comparison case-insensitive.

-- Write your query below:
SELECT *
FROM practice_job_ads
WHERE title ILIKE '%junior%'
   OR title ILIKE '%graduate%'
   OR title ILIKE '%early-career%'
ORDER BY publication_date DESC;

-- Analysis 6: Skill frequency across active advertisements
-- Expand the skills array so each skill becomes a row.
-- Count how often every skill appears in active advertisements.

-- Write your query below:
SELECT
    expanded.skill,
    COUNT(*) AS active_job_count
FROM practice_job_ads
CROSS JOIN LATERAL UNNEST(skills) AS expanded(skill)
WHERE active_status IS TRUE
GROUP BY expanded.skill
ORDER BY active_job_count DESC, expanded.skill ASC;

-- Analysis 7: Recurring skills across active advertisements
-- Return skills that occur in at least two active advertisements.

-- Write your query below:
SELECT
    expanded.skill,
    COUNT(*) AS active_job_count
FROM practice_job_ads
CROSS JOIN LATERAL UNNEST(skills) AS expanded(skill)
WHERE active_status IS TRUE
GROUP BY expanded.skill
HAVING COUNT(*) >= 2
ORDER BY active_job_count DESC, expanded.skill ASC;

-- Analysis 8: Data Engineering and Applied AI comparison
-- Compare active Data Engineering and Applied AI advertisements.
-- Return role_family, advertisement_count, distinct_employers, and distinct_cities.

-- Write your query below:
SELECT
    role_family,
    COUNT(*) AS advertisement_count,
    COUNT(DISTINCT employer) AS distinct_employers,
    COUNT(DISTINCT city) AS distinct_cities
FROM practice_job_ads
WHERE active_status IS TRUE
  AND role_family IN ('Data Engineering', 'Applied AI')
GROUP BY role_family
ORDER BY role_family;


ROLLBACK;
