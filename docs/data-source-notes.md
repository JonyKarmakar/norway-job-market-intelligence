# NAV Job Vacancy Feed Notes

## Document status

- Source reviewed: NAV Job Vacancy Feed
- Review date: 2026-07-28
- Project phase: Week 1, Day 2
- Implementation status: Documentation only

This document records the source contract understood before implementation. Exact endpoint behaviour, response schemas and operational limits will be verified again when the first NAV client is developed.

## Selected source

The project will use the NAV `pam-stilling-feed` as its initial and only vacancy source.

The deprecated `pam-public-feed` will not be used.

## Official references

- Feed documentation: <https://navikt.github.io/pam-stilling-feed/>
- API terms: <https://arbeidsplassen.nav.no/vilkar-api>
- Deprecated feed repository: <https://github.com/navikt/pam-public-feed>

Official NAV documentation will be treated as authoritative for implementation decisions.

## Why this source was selected

The feed is NAV's current official interface for receiving job-vacancy updates.

It supports the project by providing:

- Structured advertisement metadata
- Detailed advertisement records
- Advertisement identifiers
- Advertisement status
- Publication, expiry and update timestamps
- Employer and location information
- Occupation and category information
- Continuous advertisement-change events
- Incremental feed consumption

The event-based model is suitable for demonstrating ingestion, update handling, historical event retention and current-state maintenance.

## Market coverage

NAV states that its vacancy database contains a majority of publicly advertised vacancies in Norway.

Advertisements may be:

- Registered directly with NAV
- Received through third-party systems
- Received through applicant-tracking systems

FINN.no advertisements are not included.

The platform must therefore state clearly:

> The platform analyses vacancies available through NAV's feed and does not represent every vacancy in Norway.

Metrics produced by this project describe the observed NAV-feed dataset rather than the complete Norwegian labour market.

## Feed behaviour

The API is a continuous event feed rather than a conventional job-search API.

When an advertisement changes, another feed entry is generated. The latest available advertisement version represents its newest known state.

The project will distinguish between:

1. Immutable source events representing observed changes
2. The latest clean state of each advertisement

A newer event must not overwrite previously stored historical events.

## Feed event

A feed event represents a version or state change of an advertisement observed through the feed.

The feed-event identifier and advertisement UUID represent different concepts:

- The feed-event identifier identifies one feed entry.
- The advertisement UUID identifies the advertisement across multiple updates.

A repeated advertisement UUID is expected when an existing advertisement changes.

The exact uniqueness and relationship constraints will be verified using real redacted responses before the PostgreSQL schema is finalised.

## Authentication

Every API request requires authentication through the HTTP `Authorization` header:

```http
Authorization: Bearer <token>
```

NAV requires a signed JWT bearer token.

A rotating public token is available for experimentation. It:

- Rotates at irregular intervals
- Is not suitable as a stable production credential
- Must not be committed to Git
- Must not appear in documentation examples
- Must not be written to logs or test fixtures

The project will load the token from an environment variable:

```text
NAV_FEED_TOKEN
```

The `.env.example` file may contain the variable name, but it must never contain a real token.

Stable access may later require registering as a feed consumer and accepting NAV's terms.

## Pagination and incremental updates

The consumer reads the feed as a sequence of pages.

A feed-page response can include:

- The current page identifier
- The current feed URL
- An optional next-page identifier
- An optional `next_url`
- Feed items

The pipeline follows `next_url` to continue processing newer pages.

At the current end of the feed:

- `next_url` is `null`
- The next-page identifier is `null`

The consumer should continue polling the current final page until a new next page becomes available.

The pipeline must persist its progress so it can resume after a restart instead of beginning from the first page again.

Potential checkpoint information includes:

- Current feed-page identifier
- Current feed-page URL
- Last successful poll time
- Last observed `ETag`
- Last observed `Last-Modified`
- Last successful pipeline-run identifier

## Conditional requests

Feed-page responses provide the HTTP response headers:

- `ETag`
- `Last-Modified`

When polling the same page again, the client can send:

- `If-None-Match` with the previous `ETag`
- `If-Modified-Since` with the previous `Last-Modified`

When the page has not changed, the service may return:

```text
304 Not Modified
```

The pipeline must treat HTTP `304` as a successful no-change result rather than as a failure.

Conditional requests reduce unnecessary data transfer and avoid repeatedly processing an unchanged final feed page.

## Timestamp handling

Documented source fields include several timestamps, such as:

- Publication time
- Expiry time
- Advertisement update time
- Feed-event modification time
- Source-specific last-change time

The project must not assume that these timestamps are interchangeable.

The future data model should preserve separate concepts for:

- Source publication time
- Source expiry time
- Source update time
- Feed-event modification time
- Ingestion time
- First observed time
- Last observed time

Timestamp formats and timezone behaviour will be confirmed from real responses and the current OpenAPI specification.

## Active and inactive advertisements

The documented advertisement states include:

- `ACTIVE`
- `INACTIVE`

The feed contains advertisements in both states.

Advertisements may become inactive because they expire, are fulfilled, are actively stopped or are otherwise unpublished.

When an advertisement is actively stopped, NAV may mask or remove fields including:

- Title
- Employer information
- Business information
- Contact information

The project must process inactive events even when fields previously used for filtering have changed or disappeared.

An inactive advertisement must:

- Be marked inactive in the current-state table
- Be excluded from currently open vacancy results
- Be excluded from open-vacancy API responses
- Not appear as active in Power BI
- Not be presented by the AI assistant as currently available
- Have unnecessary personal contact information excluded

Historical analytical records may retain the fact that an advertisement previously existed, subject to the project's retention and privacy rules.

## Available detailed fields

The official documentation shows that detailed advertisements may contain the following categories.

### Advertisement information

- UUID
- Title
- Description
- Job title
- Publication time
- Expiry time
- Update time
- Application deadline
- Application URL
- Source URL
- Source
- Link
- Status

### Employment information

- Engagement type
- Extent
- Start time
- Position count
- Sector

### Location information

One advertisement can contain multiple work locations.

Documented location fields include:

- Country
- Address
- City
- Postal code
- County
- Municipality

The analytical model must not assume that every advertisement has exactly one location.

### Employer information

Documented employer fields include:

- Name
- Organisation number
- Description
- Homepage

Employer fields may be missing or masked for stopped advertisements.

### Classification information

Documented classification structures include:

- Occupation categories
- Category type
- Category code
- Category name
- Category score

The exact category systems and enum values must be inspected before transformation models are designed.

### Contact information

The detailed advertisement can contain a `contactList` with:

- Name
- Email
- Phone
- Role
- Title

These fields are not required for the project's analytical purpose.

## Personal information and privacy decision

NAV's terms state that consumers receive personal information contained in advertisements and are responsible for lawful handling, storage limitation and deletion when the information is no longer necessary.

The project will not persist the source `contactList`.

Before a detailed advertisement payload is written to PostgreSQL, the ingestion layer will remove:

- Contact names
- Contact email addresses
- Contact telephone numbers
- Contact roles
- Contact titles

The retained source-event payload will therefore be privacy-minimised before storage.

This is a project design decision to reduce unnecessary personal-data handling. It does not change the requirement that the retained event record remains immutable after ingestion.

Personal contact data will not be included in:

- Persistent event payloads
- Clean analytical tables
- dbt models
- Power BI datasets
- FastAPI responses
- Logs
- Test fixtures
- AI retrieval
- AI prompts
- Generated AI answers

## Known limitations

### Incomplete market coverage

The source does not include every vacancy in Norway.

FINN.no advertisements are excluded, and NAV can only provide advertisements it has the opportunity to share.

### Consumer-side filtering

The stilling-feed is not a search API for the project's analytical questions.

Filtering by employer, municipality, keyword, language, skill and role family must be implemented by the project.

### Changing and masked fields

Fields may change during an advertisement's lifetime.

Stopped advertisements may have title, employer, business or contact information removed or masked.

The pipeline must not rely on these fields remaining populated.

### Missing and inconsistent fields

Location, language, experience and skill information may be absent, unstructured or expressed only in free text.

Derived classifications must be labelled as derived rather than source-provided facts.

### Public-token instability

The experimental public token rotates at irregular intervals.

The project must handle authentication failure clearly and must not assume that the experimental token remains valid.

### Rate limits

A numerical request-rate limit was not identified in the reviewed feed documentation.

The project will therefore:

- Avoid aggressive polling
- Use conditional requests
- Use timeouts
- Add retry backoff
- Record HTTP failures
- Confirm operational limits before scheduling frequent ingestion

## Implications for the data model

The initial design should separate three concerns.

### Immutable source events

A raw-event table should retain:

- Feed-event identifier
- Advertisement UUID
- Advertisement status
- Source modification timestamp
- Feed-page identifier
- Ingestion timestamp
- Privacy-minimised JSON payload
- Payload hash
- Privacy-minimisation indicator

Raw events should be append-only.

### Current advertisement state

A separate current-state table should contain the latest known clean record for each advertisement UUID.

A newer event can update this table without modifying historical events.

The current-state table must retain whether the advertisement is active or inactive.

### Feed progress

A metadata table should retain enough information to resume polling safely.

Potential fields include:

- Feed-page identifier
- Feed-page URL
- `ETag`
- `Last-Modified`
- First poll time
- Last poll time
- Last successful pipeline run
- Last HTTP status
- Consecutive failure count

The final schema will be designed during Day 3.

## Source-contract summary

| Concern | Current understanding | Project response |
|---|---|---|
| Source | NAV `pam-stilling-feed` | Use as the only MVP vacancy source |
| Feed model | Event-based | Retain separate events and current state |
| Advertisement identity | Advertisement UUID | Use as the current-state business key |
| Event identity | Feed-item ID | Preserve for event uniqueness |
| Status | `ACTIVE` or `INACTIVE` | Maintain status and exclude inactive open listings |
| Authentication | Bearer JWT | Load token from environment |
| Experimental access | Rotating public token | Use only locally and never commit it |
| Pagination | Follow `next_url` | Persist page progress |
| End of feed | `next_url` and next ID become `null` | Poll the current final page |
| Change detection | `ETag` and `Last-Modified` | Use conditional requests |
| Unchanged page | HTTP `304` | Treat as successful no-change polling |
| Filtering | Consumer-side | Implement after ingestion |
| Contact data | May appear in `contactList` | Remove before persistent storage |
| Market coverage | Incomplete | Publish explicit coverage limitation |
| FINN.no | Excluded | Do not imply complete market coverage |
| Numerical rate limit | Not confirmed | Use cautious polling and document later |
| Schema stability | Must be verified | Validate responses and detect changes |

## Answers to source-contract questions

### What does the feed provide?

It provides a continuous stream of NAV job-advertisement events, summary metadata and URLs for retrieving current detailed advertisement data.

### What does it not provide?

It does not provide complete coverage of all Norwegian vacancies, does not include FINN.no advertisements and does not perform all desired analytical filtering for the consumer.

### What is a feed event?

A feed event is an entry representing a version or state change of an advertisement.

### What happens when an advertisement changes?

A new feed entry is generated. The newest detailed advertisement represents the current state.

### How are active and inactive advertisements represented?

The advertisement status is represented as `ACTIVE` or `INACTIVE`. Both states occur in the continuous feed.

### How does authentication work?

Every request uses a signed JWT in the HTTP Bearer authorization header. A rotating public token is available for experiments, while stable access requires consumer registration.

### How can the pipeline continue from its previous position?

It can persist the current feed-page URL or identifier and the associated conditional-request metadata, then resume from that checkpoint after a restart.

### What are `next_url`, `ETag` and `Last-Modified` used for?

`next_url` identifies the next feed page. `ETag` and `Last-Modified` describe the current page version and support conditional polling.

### Which personal data appears in a detailed advertisement?

The documented contact list can include a person's name, email address, telephone number, role and title.

### What must the project do when an advertisement becomes inactive?

It must update the advertisement's current state, remove it from current-open-vacancy outputs and ensure unnecessary contact information is not exposed or retained.

### Why should raw events be stored separately from current advertisement state?

Events preserve change history and support replay, auditing and debugging. The current-state table provides one latest record per advertisement for operational and analytical use.

### Why can the project not claim to represent the complete Norwegian job market?

NAV does not receive every publicly advertised vacancy, and FINN.no advertisements are explicitly excluded.

## Questions to investigate later

Before or during implementation, confirm:

1. The exact endpoint paths in the current OpenAPI specification.
2. The exact response envelope returned by the detail endpoint.
3. Page-size behaviour and whether it is configurable.
4. All possible HTTP error responses.
5. Whether a numerical rate limit or recommended polling interval exists.
6. Retry guidance for `429` and `5xx` responses.
7. The complete set of status and category enum values.
8. The stability guarantees for feed-event IDs and advertisement UUIDs.
9. The exact relationship among `date_modified`, `updated` and `sistEndret`.
10. Whether schema or feed-version changes are announced programmatically.
11. A justified retention period for privacy-minimised source events.
12. Whether additional fields require removal or transformation for privacy.
13. How advertisements with multiple work locations should be modelled.
14. How deleted, masked and incomplete detailed responses differ.
15. Which redacted example response can be safely committed as a test fixture.
