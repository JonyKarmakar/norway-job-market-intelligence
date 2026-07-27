# Norway Job Market Intelligence Platform

## 1. Project Overview

The Norway Job Market Intelligence Platform is an end-to-end Data Engineering, Analytics and Applied AI portfolio project.

The platform will collect Norwegian job advertisements, store historical job data, transform the raw information into reliable analytical models, visualise hiring patterns and provide a grounded AI assistant for exploring the Norwegian technology job market.

The project is designed primarily as a professional portfolio project for roles such as:

* Junior Data Engineer
* Analytics Engineer
* Data Platform Developer
* Data Integration Developer
* Data and AI Developer
* Applied AI Developer
* AI Application Developer
* Technical Data Analyst
* BI Developer
* Research Data Engineer

The project should demonstrate practical engineering ability rather than only exploratory analysis in a notebook.

---

# 2. Core Problem

Job seekers in Norway often need to manually review many advertisements to understand:

* which skills employers request
* which roles are growing
* which cities have relevant opportunities
* which jobs accept English
* how requirements differ across Data Engineering, Analytics, Applied AI and Computer Vision
* which technologies frequently appear together
* which vacancies appear suitable for graduates or early-career candidates

The available information is fragmented across individual job advertisements.

The platform will transform vacancy data into structured and searchable labour-market intelligence.

---

# 3. Target Users

## Primary users

* international job seekers in Norway
* Data Science and Computer Science graduates
* junior technology professionals
* career changers entering data or AI
* students preparing for the Norwegian job market

## Secondary users

* university career advisers
* training providers
* recruiters
* workforce-planning teams
* researchers studying technology-skill demand

The first version does not require user accounts. The target users guide the design, but the initial product can remain a portfolio demonstration.

---

# 4. Main Questions the Platform Should Answer

The platform should eventually answer questions such as:

* How many Data Engineering, Applied AI, Analytics and Computer Vision vacancies are available?
* Which locations have the highest number of relevant technology jobs?
* Which vacancies mention English as a working language?
* Which skills are most frequently requested?
* How frequently do Python, SQL, Azure, Fabric, Databricks, dbt, Power BI, RAG, Copilot Studio and Docker appear?
* Which technologies commonly appear together?
* Which employers advertise the most relevant positions?
* What experience levels are requested?
* Which vacancies mention graduate, junior or early-career opportunities?
* How are skill requirements changing over time?
* What are the differences between Data Engineer, Analytics Engineer and Applied AI Engineer advertisements?

---

# 5. Main Project Domains

The project connects three major domains.

## 5.1 Data Engineering

The platform will demonstrate:

* data extraction
* API ingestion
* raw-data storage
* incremental loading
* duplicate handling
* ETL and ELT workflows
* data modelling
* data validation
* orchestration
* logging
* testing
* data lineage
* pipeline reliability

## 5.2 Analytics Engineering and BI

The platform will demonstrate:

* clean analytical models
* fact and dimension tables
* reusable business metrics
* dbt transformations
* dbt testing
* documentation
* Power BI reporting
* trend analysis
* skill-demand analysis
* location and language analysis

## 5.3 Applied AI

The platform will demonstrate:

* structured information extraction
* job-skill classification
* grounded question answering
* retrieval over vacancy data
* evidence-backed answers
* structured outputs
* AI evaluation
* hallucination control
* fallback behaviour
* privacy and security awareness

---

# 6. Planned Data Source

The initial data source will be the official NAV job-vacancy feed.

The platform will use the source to collect structured job-advertisement records.

The first version will not scrape FINN, LinkedIn or private company websites.

## Data-source principles

* preserve the original raw response
* record when the data was ingested
* preserve advertisement identifiers
* handle updates to existing advertisements
* avoid hard-coding access credentials
* avoid exposing personal recruiter contact information
* document missing or incomplete source fields
* distinguish source facts from information inferred by AI

---

# 7. High-Level Architecture

```text
NAV Job Vacancy Feed
          │
          ▼
Python Ingestion Service
          │
          ▼
Raw PostgreSQL Storage
          │
          ▼
dbt Transformation Layer
          │
          ▼
Validated Analytical Models
          │
     ┌────┼───────────────┐
     │    │               │
     ▼    ▼               ▼
Power BI  FastAPI         AI Retrieval Layer
Dashboard API             and Grounded Assistant
          │               │
          └───────┬───────┘
                  ▼
        Recruiter-Friendly Demo
```

Prefect will orchestrate the ingestion and transformation workflow.

Docker Compose will provide the local development environment.

GitHub Actions will run automated checks.

Microsoft Fabric may be added later as a small cloud extension, but the core project must work locally first.

---

# 8. Technical Stack

## 8.1 Programming and Query Languages

### Python

Used for:

* API ingestion
* data parsing
* validation
* logging
* skill extraction
* AI integration
* FastAPI endpoints
* pipeline tests

### SQL

Used for:

* database queries
* transformations
* analytical models
* data-quality checks
* reporting datasets
* interview-relevant practice

---

## 8.2 Database

### PostgreSQL

Used as the primary local database.

It will store:

* raw source events
* cleaned job advertisements
* employers
* locations
* occupations
* skills
* job-to-skill relationships
* pipeline metadata
* AI evaluation results where appropriate

PostgreSQL is selected because it demonstrates relational modelling, SQL and database-backed application development.

---

## 8.3 Data Transformation

### dbt

Used for:

* staging models
* intermediate transformations
* analytical marts
* documentation
* relationship tests
* uniqueness tests
* null checks
* accepted-value tests
* source freshness concepts

Planned dbt layers:

```text
Raw source tables
        ↓
Staging models
        ↓
Intermediate models
        ↓
Analytical marts
```

Example models may include:

* `stg_job_ads`
* `stg_employers`
* `stg_locations`
* `int_job_ad_skills`
* `dim_employers`
* `dim_locations`
* `dim_skills`
* `fact_job_ads`
* `mart_skill_demand`
* `mart_language_accessibility`
* `mart_role_location_summary`

---

## 8.4 Workflow Orchestration

### Prefect

Used for:

* scheduled ingestion
* task dependencies
* retries
* error handling
* logging
* execution tracking
* pipeline status
* failed-task recovery

A simplified flow may be:

```text
Fetch feed
    ↓
Validate response
    ↓
Save raw events
    ↓
Update current advertisements
    ↓
Run dbt transformations
    ↓
Run quality checks
    ↓
Record pipeline result
```

Prefect is selected instead of learning Airflow, Dagster and Prefect simultaneously.

---

## 8.5 API Layer

### FastAPI

Used for:

* exposing filtered vacancy data
* retrieving analytical summaries
* supporting the AI assistant
* returning structured JSON
* providing health checks
* presenting pipeline status
* supporting future Copilot Studio integration

Possible endpoints:

```text
GET /health

GET /jobs
GET /jobs/{job_id}

GET /analytics/skills
GET /analytics/locations
GET /analytics/languages
GET /analytics/role-families

POST /assistant/query
GET /pipeline/status
```

The API should remain small and focused.

---

## 8.6 Business Intelligence

### Power BI

Used to visualise:

* vacancies over time
* roles by domain
* jobs by city and county
* English-friendly vacancies
* commonly requested skills
* skill combinations
* employers with frequent advertisements
* junior versus experienced roles
* Data Engineering versus Applied AI requirements

The dashboard should be recruiter-friendly and limited to a few clear pages.

Possible dashboard pages:

1. Market Overview
2. Skills and Technologies
3. Locations and Language
4. Role Comparison
5. Early-Career Opportunities

---

## 8.7 Applied AI Layer

The initial AI component should be narrow and reliable.

Possible responsibilities:

* extract technical skills from job descriptions
* classify advertisements into career domains
* identify likely experience levels
* answer questions using stored vacancy data
* provide advertisement identifiers or evidence with answers
* state when available data is insufficient

The AI assistant should not:

* apply for jobs
* rewrite CVs automatically
* make unsupported salary claims
* invent employer information
* recommend a job without showing the supporting data
* act as an uncontrolled autonomous agent

---

## 8.8 Retrieval and Grounding

The assistant may use a combination of:

* SQL retrieval for structured questions
* semantic retrieval for job-description text
* metadata filtering
* structured LLM output
* evidence references

Examples:

### Structured question

> Which cities have the most Data Engineering vacancies?

This should use SQL.

### Textual question

> What skills do employers commonly expect from junior AI Engineers?

This may use retrieved advertisement text and aggregated structured data.

The assistant should distinguish between:

* database facts
* retrieved advertisement evidence
* generated interpretation

---

## 8.9 AI Provider

The architecture should not depend permanently on one model provider.

The first implementation may use one of:

* OpenAI
* Claude
* Azure OpenAI
* a local Ollama-compatible model

Only one provider is needed for the first version.

The provider should be isolated behind a small interface so it can be replaced later.

The professional identity demonstrated by the project is AI application development, not expertise in one model brand.

---

## 8.10 Testing

### pytest

Used for:

* ingestion functions
* parsing
* duplicate handling
* validation
* API endpoints
* skill-normalisation rules
* AI response structure

### dbt tests

Used for:

* uniqueness
* non-null constraints
* accepted values
* referential integrity
* source relationships

### AI evaluation tests

Used for:

* correct evidence retrieval
* unsupported-answer detection
* classification accuracy
* structured-output validity
* refusal when evidence is missing
* consistency across repeated questions

---

## 8.11 Infrastructure

### Docker Compose

Used for:

* PostgreSQL
* FastAPI service
* future Prefect services where appropriate
* reproducible local setup

### GitHub Actions

Used for:

* Python tests
* linting
* dbt checks
* API tests
* build validation

### Environment variables

Used for:

* database credentials
* NAV access token
* model-provider key
* application configuration

Secrets must never be committed to GitHub.

---

## 8.12 Optional Microsoft Extension

After the local system is stable, one small Microsoft extension may be added.

Possible options:

* load a clean analytical table into Microsoft Fabric
* create a Fabric lakehouse
* rebuild one transformation in a Fabric notebook
* connect Power BI to Fabric
* expose the FastAPI service to Copilot Studio
* create a Power Automate alert for new high-match vacancies

Only one Microsoft extension is required.

The extension should demonstrate awareness of the Microsoft data and AI ecosystem without replacing the working local architecture.

---

# 9. Planned Data Model

## 9.1 Raw Layer

### `raw_job_ad_events`

Stores every downloaded source event.

Possible fields:

* event_id
* source_job_id
* source_updated_at
* ingested_at
* event_type
* raw_payload
* payload_hash

This layer preserves source history and supports reprocessing.

---

## 9.2 Core Clean Tables

### `job_ads`

* job_id
* title
* description
* employer_id
* location_id
* occupation
* employment_type
* publication_date
* expiry_date
* working_language
* experience_text
* active_status
* source_url
* first_seen_at
* last_seen_at

### `employers`

* employer_id
* employer_name
* organisation_number where available
* sector
* industry

### `locations`

* location_id
* city
* municipality
* county
* country

### `skills`

* skill_id
* canonical_skill_name
* skill_category
* aliases

### `job_ad_skills`

* job_id
* skill_id
* extraction_method
* confidence
* evidence_text

---

## 9.3 Optional Supporting Tables

### `role_families`

Possible values:

* Data Engineering
* Applied AI
* Analytics
* Computer Vision
* Software Engineering
* Other

### `experience_levels`

Possible values:

* Graduate
* Junior
* Early Career
* Mid-Level
* Senior
* Unclear

### `pipeline_runs`

* run_id
* started_at
* completed_at
* status
* records_received
* records_inserted
* records_updated
* records_failed
* error_message

---

# 10. Skills Covered by the Project

## 10.1 Data Engineering Skills

* Python data ingestion
* REST API integration
* JSON processing
* PostgreSQL
* SQL
* ETL and ELT
* incremental loading
* idempotency
* duplicate handling
* schema design
* dimensional modelling
* raw and transformed data separation
* pipeline orchestration
* retries
* logging
* data freshness
* data-quality testing
* pipeline monitoring
* Docker
* CI/CD

---

## 10.2 Analytics Engineering Skills

* dbt
* staging models
* intermediate models
* data marts
* fact and dimension tables
* business metrics
* source documentation
* lineage
* transformation tests
* reproducible analytical models
* semantic consistency
* stakeholder-oriented data products

---

## 10.3 Data Analytics Skills

* Power BI
* KPI design
* dashboard development
* trend analysis
* skill-demand analysis
* location analysis
* language analysis
* job-role comparison
* data storytelling
* communicating limitations
* explaining findings to non-technical users

---

## 10.4 Applied AI Skills

* LLM API integration
* structured outputs
* skill extraction
* text classification
* retrieval
* RAG fundamentals
* grounding
* evidence-backed responses
* guardrails
* fallback responses
* hallucination detection
* evaluation datasets
* prompt testing
* model-provider abstraction
* human-readable explanations

---

## 10.5 Software Engineering Skills

* modular Python
* FastAPI
* REST endpoints
* type hints
* configuration management
* error handling
* testing
* Git
* GitHub workflow
* documentation
* Docker Compose
* API contracts
* logging
* maintainable repository structure

---

## 10.6 Microsoft Ecosystem Skills

Depending on the optional extension:

* Microsoft Fabric
* OneLake
* Fabric lakehouse
* Fabric pipelines
* Power BI integration
* Copilot Studio
* Power Automate
* custom API connectors
* Microsoft data and AI architecture awareness

---

# 11. Project Development Phases

## Phase 1 — Foundation

* create repository
* write project brief
* understand source
* design architecture
* design initial data model
* create local PostgreSQL
* practise SQL

## Phase 2 — Ingestion

* authenticate with the source
* retrieve records
* validate responses
* save raw events
* prevent duplicates
* handle updates
* record pipeline metadata

## Phase 3 — Transformation

* create dbt project
* build staging models
* create clean tables
* normalise employers and locations
* create fact and dimension models
* add tests
* generate documentation

## Phase 4 — Orchestration

* build Prefect flows
* schedule ingestion
* add retries
* record logs
* run dbt automatically
* expose pipeline status

## Phase 5 — Analytics

* define KPIs
* build Power BI model
* create dashboard pages
* validate calculations
* document limitations

## Phase 6 — Applied AI

* extract skills
* classify role families
* add grounded question answering
* return evidence
* create an evaluation dataset
* test unsupported questions

## Phase 7 — Microsoft Extension

Choose one:

* Fabric
* Copilot Studio
* Power Automate

## Phase 8 — Portfolio Packaging

* polish README
* create architecture diagram
* create data-model diagram
* record demo
* prepare screenshots
* publish testing summary
* publish AI evaluation results
* write one-page case study

---

# 12. Minimum Viable Product

The MVP is complete when the project can:

1. Retrieve job-advertisement data.
2. Store raw records in PostgreSQL.
3. Maintain clean current advertisement records.
4. Transform data using dbt.
5. Run data-quality tests.
6. Schedule the workflow using Prefect.
7. Present job-market insights in Power BI.
8. Answer a limited set of questions using grounded evidence.
9. Run through Docker.
10. Pass automated tests in GitHub Actions.

---

# 13. Project Boundaries

The first version will not include:

* automatic job applications
* automatic CV rewriting
* user accounts
* paid subscriptions
* a mobile application
* a large React frontend
* scraping many websites
* Kafka
* Kubernetes
* several cloud platforms
* several LLM providers
* multi-agent orchestration
* complex recommendation algorithms
* advanced personalisation
* production-scale infrastructure

These are intentionally excluded to ensure the project is finished.

---

# 14. Privacy, Security and Responsible AI

The project should demonstrate professional awareness of:

* access-token security
* environment-variable management
* avoiding personal contact-data exposure
* minimising stored sensitive information
* documenting data provenance
* separating source facts from AI interpretation
* preventing unsupported answers
* returning uncertainty when evidence is insufficient
* logging AI evaluation results
* documenting known limitations
* avoiding automated decisions about candidates

The project analyses job advertisements. It should not rank or assess individual job seekers.

---

# 15. Evaluation Plan

## Data Pipeline Evaluation

Track:

* records received
* records inserted
* records updated
* duplicate records
* invalid records
* missing important fields
* failed pipeline runs
* average pipeline duration

## Data Quality Evaluation

Track:

* uniqueness-test results
* relationship-test results
* null rates
* unexpected category values
* stale data
* source-schema changes

## AI Evaluation

Create a small test set containing questions such as:

* Which skills are most requested for Data Engineers?
* Which locations have the most English-friendly AI vacancies?
* Are there advertisements that mention Copilot Studio?
* Which roles appear suitable for graduates?
* What information cannot be determined from the available data?

Evaluate:

* retrieval correctness
* evidence quality
* answer faithfulness
* unsupported claims
* structured-output validity
* fallback correctness
* response latency
* approximate model cost where relevant

---

# 16. Portfolio Evidence

The final project should contain:

* public GitHub repository
* professional README
* architecture diagram
* data-model diagram
* dbt lineage screenshot
* Power BI screenshots
* pipeline execution screenshot
* automated test summary
* AI evaluation table
* two-minute demonstration video
* one-page project case study
* documented limitations
* clear setup instructions

The repository should make the project understandable within two minutes.

---

# 17. Success Metrics

Use real measurements only.

Possible metrics include:

* number of advertisements processed
* number of employers represented
* number of locations represented
* number of identified skills
* number of dbt models
* number of dbt tests
* pipeline execution time
* duplicate-prevention rate
* percentage of records passing validation
* number of AI evaluation questions
* percentage of evidence-supported answers
* number of unsupported questions correctly rejected

Do not invent business-impact figures.

---

# 18. Final Professional Story

The completed project should support a statement such as:

> Developed an end-to-end Norwegian job-market intelligence platform using Python, PostgreSQL, dbt, Prefect, FastAPI, Power BI and Docker. Built incremental ingestion and tested analytical models for analysing job roles, locations, languages and technology demand. Added grounded AI question answering with evidence references, evaluation checks and fallback behaviour for unsupported questions.

---

# 19. Connection to the Existing Portfolio

## VisionCommand AI

Demonstrates:

* Computer Vision
* multimodal AI
* LLM integration
* FastAPI
* React
* PostgreSQL
* Docker
* AI evaluation
* product-oriented software development

## Norway Job Market Intelligence Platform

Demonstrates:

* Data Engineering
* Analytics Engineering
* SQL
* dbt
* orchestration
* Power BI
* Microsoft data-platform awareness
* grounded AI
* pipeline reliability

Together, the two projects position the candidate for both Data Engineering and Applied AI opportunities.

---

# 20. Project Identity

## Project name

**Norway Job Market Intelligence Platform**

## One-line description

An end-to-end data and AI platform for analysing Norwegian technology-job demand using reliable pipelines, tested analytical models, Power BI and grounded AI.

## Repository name

```text
norway-job-market-intelligence
```
