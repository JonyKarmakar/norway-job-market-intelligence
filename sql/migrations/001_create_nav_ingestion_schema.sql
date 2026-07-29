BEGIN;

CREATE TABLE nav_feed_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY,
    source_event_id TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    feed_page_id TEXT,
    source_status TEXT,
    source_updated_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash TEXT NOT NULL,
    payload JSONB NOT NULL,
    contact_data_removed BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_nav_feed_events
        PRIMARY KEY (event_id),

    CONSTRAINT uq_nav_feed_events_source_event_id
        UNIQUE (source_event_id),

    CONSTRAINT uq_nav_feed_events_event_job
        UNIQUE (event_id, source_job_id),

    CONSTRAINT ck_nav_feed_events_source_event_id_not_blank
        CHECK (BTRIM(source_event_id) <> ''),

    CONSTRAINT ck_nav_feed_events_source_job_id_not_blank
        CHECK (BTRIM(source_job_id) <> ''),

    CONSTRAINT ck_nav_feed_events_payload_hash_not_blank
        CHECK (BTRIM(payload_hash) <> ''),

    CONSTRAINT ck_nav_feed_events_payload_object
        CHECK (JSONB_TYPEOF(payload) = 'object'),

    CONSTRAINT ck_nav_feed_events_contact_data_removed
        CHECK (contact_data_removed IS TRUE),

    CONSTRAINT ck_nav_feed_events_no_contact_list
        CHECK (NOT (payload ? 'contactList'))
);

CREATE INDEX idx_nav_feed_events_source_job_id
    ON nav_feed_events (source_job_id);

CREATE INDEX idx_nav_feed_events_source_updated_at
    ON nav_feed_events (source_updated_at);

CREATE INDEX idx_nav_feed_events_ingested_at
    ON nav_feed_events (ingested_at);

CREATE TABLE job_advertisements_current (
    source_job_id TEXT,
    latest_event_id BIGINT NOT NULL,
    source_status TEXT NOT NULL,
    source_updated_at TIMESTAMPTZ,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    current_payload JSONB NOT NULL,

    CONSTRAINT pk_job_advertisements_current
        PRIMARY KEY (source_job_id),

    CONSTRAINT fk_job_advertisements_current_latest_event
        FOREIGN KEY (latest_event_id, source_job_id)
        REFERENCES nav_feed_events (event_id, source_job_id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_job_advertisements_current_source_job_id_not_blank
        CHECK (BTRIM(source_job_id) <> ''),

    CONSTRAINT ck_job_advertisements_current_source_status_not_blank
        CHECK (BTRIM(source_status) <> ''),

    CONSTRAINT ck_job_advertisements_current_seen_order
        CHECK (last_seen_at >= first_seen_at),

    CONSTRAINT ck_job_advertisements_current_payload_object
        CHECK (JSONB_TYPEOF(current_payload) = 'object'),

    CONSTRAINT ck_job_advertisements_current_no_contact_list
        CHECK (NOT (current_payload ? 'contactList'))
);

CREATE INDEX idx_job_advertisements_current_source_status
    ON job_advertisements_current (source_status);

CREATE INDEX idx_job_advertisements_current_source_updated_at
    ON job_advertisements_current (source_updated_at);

CREATE TABLE nav_feed_progress (
    feed_name TEXT,
    next_url TEXT,
    etag TEXT,
    last_modified TEXT,
    last_successful_poll_at TIMESTAMPTZ,
    last_event_source_time TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_nav_feed_progress
        PRIMARY KEY (feed_name),

    CONSTRAINT ck_nav_feed_progress_feed_name_not_blank
        CHECK (BTRIM(feed_name) <> '')
);

COMMIT;
