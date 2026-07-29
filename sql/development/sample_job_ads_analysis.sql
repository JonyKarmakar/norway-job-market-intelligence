\set ON_ERROR_STOP on

-- Purpose:
-- Demonstrate PostgreSQL analytical patterns using a small synthetic
-- Norway-focused job advertisement dataset.
--
-- Coverage:
-- Filtering, aggregation, conditional aggregation, arrays, CTEs,
-- window functions, ranking, duplicate detection and date bucketing.
--
-- Safety:
-- All objects are temporary and the transaction ends with ROLLBACK.
-- No real vacancy or personal contact data is used.

BEGIN;

DROP TABLE IF EXISTS synthetic_job_ads;

CREATE TEMP TABLE synthetic_job_ads (
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

INSERT INTO synthetic_job_ads (
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

SELECT *
FROM synthetic_job_ads
WHERE active_status IS TRUE
ORDER BY publication_date DESC;

-- Analysis 2: Active advertisement volume by role family
-- Count active advertisements by role_family.
-- Sort from the highest count to the lowest.

SELECT role_family, COUNT(*) AS active_job_count
FROM synthetic_job_ads
WHERE active_status IS TRUE
GROUP BY role_family
ORDER BY active_job_count DESC;

-- Analysis 3: Active advertisements supporting English
-- Return active advertisements that can be worked in English.
-- Hint: the field may contain either "English" or "English and Norwegian".

SELECT *
FROM synthetic_job_ads
WHERE active_status IS TRUE
  AND working_language LIKE '%English%'
ORDER BY publication_date DESC;

-- Analysis 4: Active advertisement volume by city
-- Count active advertisements by city.
-- Place missing cities in a visible "Unknown" category.

SELECT
    COALESCE(city, 'Unknown') AS city,
    COUNT(*) AS active_job_count
FROM synthetic_job_ads
WHERE active_status IS TRUE
GROUP BY COALESCE(city, 'Unknown')
ORDER BY active_job_count DESC, city ASC;

-- Analysis 5: Early-career advertisement identification
-- Return advertisements whose title suggests a junior, graduate, or early-career role.
-- Make the title comparison case-insensitive.

SELECT *
FROM synthetic_job_ads
WHERE title ILIKE '%junior%'
   OR title ILIKE '%graduate%'
   OR title ILIKE '%early-career%'
ORDER BY publication_date DESC;

-- Analysis 6: Skill frequency across active advertisements
-- Expand the skills array so each skill becomes a row.
-- Count how often every skill appears in active advertisements.

SELECT
    expanded.skill,
    COUNT(*) AS active_job_count
FROM synthetic_job_ads
CROSS JOIN LATERAL UNNEST(skills) AS expanded(skill)
WHERE active_status IS TRUE
GROUP BY expanded.skill
ORDER BY active_job_count DESC, expanded.skill ASC;

-- Analysis 7: Recurring skills across active advertisements
-- Return skills that occur in at least two active advertisements.

SELECT
    expanded.skill,
    COUNT(*) AS active_job_count
FROM synthetic_job_ads
CROSS JOIN LATERAL UNNEST(skills) AS expanded(skill)
WHERE active_status IS TRUE
GROUP BY expanded.skill
HAVING COUNT(*) >= 2
ORDER BY active_job_count DESC, expanded.skill ASC;

-- Analysis 8: Data Engineering and Applied AI comparison
-- Compare active Data Engineering and Applied AI advertisements.
-- Return role_family, advertisement_count, distinct_employers, and distinct_cities.

SELECT
    role_family,
    COUNT(*) AS advertisement_count,
    COUNT(DISTINCT employer) AS distinct_employers,
    COUNT(DISTINCT city) AS distinct_cities
FROM synthetic_job_ads
WHERE active_status IS TRUE
  AND role_family IN ('Data Engineering', 'Applied AI')
GROUP BY role_family
ORDER BY role_family;

-- Analysis 9: Advertisement status composition by role family
-- Return total, active, and inactive advertisement counts for each role family.

SELECT
    role_family,
    COUNT(*) AS total_advertisements,
    COUNT(*) FILTER (
        WHERE active_status IS TRUE
    ) AS active_advertisements,
    COUNT(*) FILTER (
        WHERE active_status IS FALSE
    ) AS inactive_advertisements
FROM synthetic_job_ads
GROUP BY role_family
ORDER BY role_family;

-- Analysis 10: Active advertisement percentage by role family
-- Return total and active advertisement counts for each role family.
-- Calculate the percentage of advertisements that are active.
-- Round the percentage to one decimal place.

SELECT
    role_family,
    COUNT(*) AS total_advertisements,
    COUNT(*) FILTER (
        WHERE active_status IS TRUE
    ) AS active_advertisements,
    ROUND(
        100.0
        * COUNT(*) FILTER (WHERE active_status IS TRUE)
        / COUNT(*),
        1
    ) AS active_percentage
FROM synthetic_job_ads
GROUP BY role_family
ORDER BY role_family;

-- Analysis 11: Active percentage using a common table expression
-- Calculate advertisement counts inside a CTE.
-- Use the calculated columns to produce the active percentage.
-- Return one row for each role family.

WITH role_family_status_counts AS (
    SELECT
        role_family,
        COUNT(*) AS total_advertisements,
        COUNT(*) FILTER (
            WHERE active_status IS TRUE
        ) AS active_advertisements
    FROM synthetic_job_ads
    GROUP BY role_family
)
SELECT
    role_family,
    total_advertisements,
    active_advertisements,
    ROUND(
        100.0 * active_advertisements / total_advertisements,
        1
    ) AS active_percentage
FROM role_family_status_counts
ORDER BY role_family;

-- Analysis 12: Rank role families by active advertisement volume
-- Count active advertisements for each role family.
-- Assign the same rank to role families with equal active counts.
-- Do not leave gaps between ranking values.

WITH role_family_activity AS (
    SELECT
        role_family,
        COUNT(*) FILTER (
            WHERE active_status IS TRUE
        ) AS active_advertisements
    FROM synthetic_job_ads
    GROUP BY role_family
)
SELECT
    role_family,
    active_advertisements,
    DENSE_RANK() OVER (
        ORDER BY active_advertisements DESC
    ) AS activity_rank
FROM role_family_activity
ORDER BY activity_rank, role_family;

-- Analysis 13: Advertisement recency within each role family
-- Number active advertisements separately within each role family.
-- Assign position 1 to the newest advertisement in each role family.
-- Return the role family, title, publication date, and recency position.

SELECT
    role_family,
    title,
    publication_date,
    ROW_NUMBER() OVER (
        PARTITION BY role_family
        ORDER BY publication_date DESC
    ) AS recency_position
FROM synthetic_job_ads
WHERE active_status IS TRUE
ORDER BY role_family, recency_position;

-- Analysis 14: Newest active advertisement by role family
-- Rank active advertisements by publication date within each role family.
-- Return only the newest advertisement from each role family.
-- Include the role family, title, employer, publication date, and position.

WITH ranked_active_advertisements AS (
    SELECT
        role_family,
        title,
        employer,
        publication_date,
        ROW_NUMBER() OVER (
            PARTITION BY role_family
            ORDER BY publication_date DESC
        ) AS recency_position
    FROM synthetic_job_ads
    WHERE active_status IS TRUE
)
SELECT
    role_family,
    title,
    employer,
    publication_date,
    recency_position
FROM ranked_active_advertisements
WHERE recency_position = 1
ORDER BY role_family;

-- Analysis 15: Time between advertisements within each role family
-- Compare each active advertisement with the previously published
-- advertisement in the same role family.
-- Calculate the number of days since the previous advertisement.

WITH advertisements_with_previous_date AS (
    SELECT
        role_family,
        title,
        publication_date,
        LAG(publication_date) OVER (
            PARTITION BY role_family
            ORDER BY publication_date ASC
        ) AS previous_publication_date
    FROM synthetic_job_ads
    WHERE active_status IS TRUE
)
SELECT
    role_family,
    title,
    publication_date,
    previous_publication_date,
    publication_date - previous_publication_date AS days_since_previous
FROM advertisements_with_previous_date
ORDER BY role_family, publication_date;

-- Analysis 16: Cumulative advertisement count by role family
-- Count active advertisements chronologically within each role family.
-- Return the role family, title, publication date, and cumulative count.

SELECT
    role_family,
    title,
    publication_date,
    COUNT(*) OVER (
        PARTITION BY role_family
        ORDER BY publication_date ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_advertisements
FROM synthetic_job_ads
WHERE active_status IS TRUE
ORDER BY role_family, publication_date;

-- Analysis 17: Employer ranking by advertisement volume
-- Count advertisements for each employer.
-- Rank employers from the highest advertisement count to the lowest.
-- Assign the same rank to employers with equal counts.

WITH employer_advertisement_counts AS (
    SELECT
        employer,
        COUNT(*) AS advertisement_count
    FROM synthetic_job_ads
    GROUP BY employer
)
SELECT
    employer,
    advertisement_count,
    DENSE_RANK() OVER (
        ORDER BY advertisement_count DESC
    ) AS employer_rank
FROM employer_advertisement_counts
ORDER BY employer_rank, employer;

-- Analysis 18: Advertisement distribution by city
-- Count advertisements for each city.
-- Place missing cities in an Unknown category.
-- Calculate each city's percentage share of all advertisements.
-- Round the percentage to one decimal place.

WITH city_advertisement_counts AS (
    SELECT
        COALESCE(city, 'Unknown') AS city,
        COUNT(*) AS advertisement_count
    FROM synthetic_job_ads
    GROUP BY COALESCE(city, 'Unknown')
)
SELECT
    city,
    advertisement_count,
    ROUND(
        100.0 * advertisement_count
        / SUM(advertisement_count) OVER (),
        1
    ) AS advertisement_percentage
FROM city_advertisement_counts
ORDER BY advertisement_count DESC, city;

-- Analysis 19: Potential duplicate advertisements
-- Treat advertisements with the same title and employer as potential duplicates.
-- Count each title-and-employer combination.
-- Return only combinations appearing more than once.

SELECT
    title,
    employer,
    COUNT(*) AS duplicate_count
FROM synthetic_job_ads
GROUP BY title, employer
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, employer, title;

-- Analysis 20: Employer activity compared with the average
-- Count advertisements for each employer.
-- Calculate the average advertisement count across employers.
-- Classify each employer as Above average, Average, or Below average.

WITH employer_advertisement_counts AS (
    SELECT
        employer,
        COUNT(*) AS advertisement_count
    FROM synthetic_job_ads
    GROUP BY employer
),
average_employer_activity AS (
    SELECT
        AVG(advertisement_count) AS average_advertisement_count
    FROM employer_advertisement_counts
)
SELECT
    employer_counts.employer,
    employer_counts.advertisement_count,
    ROUND(
        average_activity.average_advertisement_count,
        1
    ) AS average_advertisement_count,
    CASE
        WHEN employer_counts.advertisement_count
            > average_activity.average_advertisement_count
            THEN 'Above average'
        WHEN employer_counts.advertisement_count
            = average_activity.average_advertisement_count
            THEN 'Average'
        ELSE 'Below average'
    END AS activity_comparison
FROM employer_advertisement_counts AS employer_counts
CROSS JOIN average_employer_activity AS average_activity
ORDER BY employer_counts.advertisement_count DESC, employer_counts.employer;

-- Analysis 21: Active advertisement volume by publication week
-- Count active advertisements by publication week.
-- Represent each week using its starting date.
-- Sort the result chronologically.

SELECT
    DATE_TRUNC('week', publication_date)::DATE AS week_start,
    COUNT(*) AS active_advertisement_count
FROM synthetic_job_ads
WHERE active_status IS TRUE
GROUP BY DATE_TRUNC('week', publication_date)::DATE
ORDER BY week_start;

ROLLBACK;
