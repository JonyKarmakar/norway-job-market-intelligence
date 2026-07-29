\set ON_ERROR_STOP on

BEGIN;

SET LOCAL TIME ZONE 'UTC';

INSERT INTO nav_feed_events (
    source_event_id,
    source_job_id,
    feed_page_id,
    source_status,
    source_updated_at,
    ingested_at,
    payload_hash,
    payload,
    contact_data_removed
)
VALUES (
    'synthetic-event-001',
    'synthetic-job-001',
    'synthetic-page-001',
    'ACTIVE',
    '2026-01-01 08:55:00+00',
    '2026-01-01 09:00:00+00',
    'synthetic-hash-001',
    '{"title": "Synthetic Data Engineer", "status": "ACTIVE"}',
    TRUE
);

INSERT INTO job_advertisements_current (
    source_job_id,
    latest_event_id,
    source_status,
    source_updated_at,
    first_seen_at,
    last_seen_at,
    current_payload
)
SELECT
    source_job_id,
    event_id,
    source_status,
    source_updated_at,
    '2026-01-01 09:00:00+00',
    '2026-01-01 09:00:00+00',
    payload
FROM nav_feed_events
WHERE source_event_id = 'synthetic-event-001';

INSERT INTO nav_feed_events (
    source_event_id,
    source_job_id,
    feed_page_id,
    source_status,
    source_updated_at,
    ingested_at,
    payload_hash,
    payload,
    contact_data_removed
)
VALUES (
    'synthetic-event-002',
    'synthetic-job-001',
    'synthetic-page-002',
    'ACTIVE',
    '2026-01-02 08:55:00+00',
    '2026-01-02 09:00:00+00',
    'synthetic-hash-002',
    '{"title": "Synthetic Senior Data Engineer", "status": "ACTIVE"}',
    TRUE
);

UPDATE job_advertisements_current AS current_ad
SET
    latest_event_id = event.event_id,
    source_status = event.source_status,
    source_updated_at = event.source_updated_at,
    last_seen_at = '2026-01-02 09:00:00+00',
    current_payload = event.payload
FROM nav_feed_events AS event
WHERE current_ad.source_job_id = event.source_job_id
  AND event.source_event_id = 'synthetic-event-002';

INSERT INTO nav_feed_events (
    source_event_id,
    source_job_id,
    feed_page_id,
    source_status,
    source_updated_at,
    ingested_at,
    payload_hash,
    payload,
    contact_data_removed
)
VALUES (
    'synthetic-event-003',
    'synthetic-job-001',
    'synthetic-page-003',
    'INACTIVE',
    '2026-01-03 08:55:00+00',
    '2026-01-03 09:00:00+00',
    'synthetic-hash-003',
    '{"title": "Synthetic Senior Data Engineer", "status": "INACTIVE"}',
    TRUE
);

UPDATE job_advertisements_current AS current_ad
SET
    latest_event_id = event.event_id,
    source_status = event.source_status,
    source_updated_at = event.source_updated_at,
    last_seen_at = '2026-01-03 09:00:00+00',
    current_payload = event.payload
FROM nav_feed_events AS event
WHERE current_ad.source_job_id = event.source_job_id
  AND event.source_event_id = 'synthetic-event-003';

INSERT INTO nav_feed_progress (
    feed_name,
    next_url,
    etag,
    last_modified,
    last_successful_poll_at,
    last_event_source_time,
    updated_at
)
VALUES (
    'synthetic-nav-feed',
    'https://example.invalid/feed/page-004',
    '"synthetic-etag-003"',
    'Sat, 03 Jan 2026 08:55:00 GMT',
    '2026-01-03 09:01:00+00',
    '2026-01-03 08:55:00+00',
    '2026-01-03 09:01:00+00'
);

DO $$
DECLARE
    historical_event_count INTEGER;
    current_row_count INTEGER;
    verified_status TEXT;
    verified_latest_event TEXT;
    verified_first_seen TIMESTAMPTZ;
    verified_last_seen TIMESTAMPTZ;
    verified_next_url TEXT;
BEGIN
    SELECT COUNT(*)
    INTO historical_event_count
    FROM nav_feed_events
    WHERE source_job_id = 'synthetic-job-001';

    IF historical_event_count <> 3 THEN
        RAISE EXCEPTION
            'Expected 3 historical events, found %',
            historical_event_count;
    END IF;

    SELECT COUNT(*)
    INTO current_row_count
    FROM job_advertisements_current
    WHERE source_job_id = 'synthetic-job-001';

    IF current_row_count <> 1 THEN
        RAISE EXCEPTION
            'Expected 1 current-state row, found %',
            current_row_count;
    END IF;

    SELECT
        current_ad.source_status,
        event.source_event_id,
        current_ad.first_seen_at,
        current_ad.last_seen_at
    INTO
        verified_status,
        verified_latest_event,
        verified_first_seen,
        verified_last_seen
    FROM job_advertisements_current AS current_ad
    JOIN nav_feed_events AS event
        ON event.event_id = current_ad.latest_event_id
       AND event.source_job_id = current_ad.source_job_id
    WHERE current_ad.source_job_id = 'synthetic-job-001';

    IF verified_status <> 'INACTIVE' THEN
        RAISE EXCEPTION
            'Expected final status INACTIVE, found %',
            verified_status;
    END IF;

    IF verified_latest_event <> 'synthetic-event-003' THEN
        RAISE EXCEPTION
            'Expected latest event synthetic-event-003, found %',
            verified_latest_event;
    END IF;

    IF verified_first_seen <> '2026-01-01 09:00:00+00'::TIMESTAMPTZ THEN
        RAISE EXCEPTION
            'first_seen_at was not preserved: %',
            verified_first_seen;
    END IF;

    IF verified_last_seen <> '2026-01-03 09:00:00+00'::TIMESTAMPTZ THEN
        RAISE EXCEPTION
            'Unexpected last_seen_at value: %',
            verified_last_seen;
    END IF;

    SELECT next_url
    INTO verified_next_url
    FROM nav_feed_progress
    WHERE feed_name = 'synthetic-nav-feed';

    IF verified_next_url <> 'https://example.invalid/feed/page-004' THEN
        RAISE EXCEPTION
            'Unexpected feed progress URL: %',
            verified_next_url;
    END IF;

    RAISE NOTICE 'Positive lifecycle verification passed.';
END
$$;

DO $$
DECLARE
    existing_event_id BIGINT;
    second_job_event_id BIGINT;
    third_job_event_id BIGINT;
BEGIN
    BEGIN
        INSERT INTO nav_feed_events (
            source_event_id,
            source_job_id,
            payload_hash,
            payload,
            contact_data_removed
        )
        VALUES (
            'synthetic-event-001',
            'synthetic-job-duplicate',
            'synthetic-hash-duplicate',
            '{"title": "Synthetic Duplicate Event"}',
            TRUE
        );

        RAISE EXCEPTION
            'Duplicate source_event_id was accepted unexpectedly.';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'Duplicate source_event_id rejected.';
    END;

    BEGIN
        INSERT INTO nav_feed_events (
            source_event_id,
            source_job_id,
            payload_hash,
            payload,
            contact_data_removed
        )
        VALUES (
            'synthetic-event-contact-data',
            'synthetic-job-contact-data',
            'synthetic-hash-contact-data',
            '{"title": "Synthetic Vacancy", "contactList": []}',
            TRUE
        );

        RAISE EXCEPTION
            'Event payload containing contactList was accepted unexpectedly.';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Event contactList payload rejected.';
    END;

    SELECT event_id
    INTO existing_event_id
    FROM nav_feed_events
    WHERE source_event_id = 'synthetic-event-003';

    BEGIN
        INSERT INTO job_advertisements_current (
            source_job_id,
            latest_event_id,
            source_status,
            first_seen_at,
            last_seen_at,
            current_payload
        )
        VALUES (
            'synthetic-job-mismatch',
            existing_event_id,
            'ACTIVE',
            '2026-01-04 09:00:00+00',
            '2026-01-04 09:00:00+00',
            '{"title": "Synthetic Mismatched Vacancy"}'
        );

        RAISE EXCEPTION
            'Mismatched event ownership was accepted unexpectedly.';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'Mismatched event ownership rejected.';
    END;

    INSERT INTO nav_feed_events (
        source_event_id,
        source_job_id,
        source_status,
        payload_hash,
        payload,
        contact_data_removed
    )
    VALUES (
        'synthetic-event-004',
        'synthetic-job-002',
        'ACTIVE',
        'synthetic-hash-004',
        '{"title": "Synthetic Platform Engineer"}',
        TRUE
    )
    RETURNING event_id
    INTO second_job_event_id;

    BEGIN
        INSERT INTO job_advertisements_current (
            source_job_id,
            latest_event_id,
            source_status,
            first_seen_at,
            last_seen_at,
            current_payload
        )
        VALUES (
            'synthetic-job-002',
            second_job_event_id,
            'ACTIVE',
            '2026-01-05 10:00:00+00',
            '2026-01-05 09:00:00+00',
            '{"title": "Synthetic Platform Engineer"}'
        );

        RAISE EXCEPTION
            'Invalid first_seen_at and last_seen_at order was accepted.';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid timestamp order rejected.';
    END;

    INSERT INTO nav_feed_events (
        source_event_id,
        source_job_id,
        source_status,
        payload_hash,
        payload,
        contact_data_removed
    )
    VALUES (
        'synthetic-event-005',
        'synthetic-job-003',
        'ACTIVE',
        'synthetic-hash-005',
        '{"title": "Synthetic Analytics Engineer"}',
        TRUE
    )
    RETURNING event_id
    INTO third_job_event_id;

    BEGIN
        INSERT INTO job_advertisements_current (
            source_job_id,
            latest_event_id,
            source_status,
            first_seen_at,
            last_seen_at,
            current_payload
        )
        VALUES (
            'synthetic-job-003',
            third_job_event_id,
            'ACTIVE',
            '2026-01-05 09:00:00+00',
            '2026-01-05 09:00:00+00',
            '{"title": "Synthetic Analytics Engineer", "contactList": []}'
        );

        RAISE EXCEPTION
            'Current payload containing contactList was accepted unexpectedly.';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Current-state contactList payload rejected.';
    END;

    BEGIN
        INSERT INTO nav_feed_progress (feed_name)
        VALUES ('   ');

        RAISE EXCEPTION
            'Blank feed_name was accepted unexpectedly.';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Blank feed_name rejected.';
    END;

    RAISE NOTICE 'Negative constraint verification passed.';
END
$$;

ROLLBACK;
