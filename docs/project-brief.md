# Norway Job Market Intelligence Platform

## Project purpose

The Norway Job Market Intelligence Platform is an end-to-end data and applied AI portfolio project for analysing technology-job demand in Norway.

The platform will collect vacancy events from NAV, preserve source history, maintain the latest state of each advertisement, create tested analytical models, visualise labour-market patterns and later support a narrow evidence-grounded assistant.

The project is intended to demonstrate practical Data Engineering, Analytics Engineering, Business Intelligence and AI application development.

## Problem statement

Norwegian job-market information is distributed across individual advertisements, making it difficult for job seekers to compare roles, locations, working-language requirements, experience expectations and technical skills systematically.

International graduates and early-career professionals face an additional challenge because English-language accessibility and junior suitability are not always stated consistently.

The available vacancy data must therefore be collected, structured, tested and presented carefully before reliable market-level insights can be produced.

## Proposed solution

Build a local-first data and AI platform that:

- ingests advertisement events from the NAV vacancy feed
- retains immutable privacy-minimised source events
- maintains the latest clean state of each advertisement
- handles updated and inactive advertisements
- transforms source data into tested analytical models
- analyses roles, locations, languages, experience levels and skills
- visualises selected findings in Power BI
- exposes focused data through FastAPI
- answers a limited set of questions using verifiable evidence

## Primary users

- International graduates in Norway
- Early-career data and AI professionals
- Technology job seekers
- University career advisers

## Secondary users

- Training providers
- Labour-market researchers
- Recruiters
- Workforce-planning teams

The initial version will not require user accounts. These user groups guide the analytical questions and presentation of results.

## Core analytical questions

The first complete version will focus on seven questions:

1. Which role families appear most frequently?
2. Which locations have the most vacancies?
3. Which vacancies indicate English as a working language?
4. Which technical skills appear most frequently?
5. Which skills commonly appear together?
6. Which advertisements appear suitable for graduates or junior candidates?
7. How do Data Engineering, Applied AI, Analytics and Computer Vision vacancies differ?

Additional questions may be introduced only after the source data and analytical models are understood.

## Selected data source

The initial and only vacancy source for the local MVP will be the NAV `pam-stilling-feed`.

The deprecated `pam-public-feed` will not be used.

The platform analyses advertisements available through NAV's feed. It does not represent every vacancy in Norway, and FINN.no advertisements are not included.

Detailed source behaviour, limitations and ingestion implications are documented separately in `docs/data-source-notes.md`.

## Technology direction

The planned local system uses:

- Python for ingestion, validation, APIs and AI integration
- PostgreSQL for raw, clean and operational data
- dbt for transformations, tests and analytical models
- Prefect for orchestration, retries and execution tracking
- FastAPI for focused data access
- Power BI for analytical reporting
- Docker Compose for reproducible local development
- GitHub Actions for automated checks
- One LLM provider for the grounded assistant
- One later Microsoft ecosystem extension

The complete local system must work without depending on a temporary cloud environment.

## Minimum viable product

The complete local MVP must:

1. Read feed events from the NAV vacancy feed.
2. Store privacy-minimised source-event payloads in PostgreSQL.
3. Maintain the latest clean state of each advertisement.
4. Handle advertisement updates and inactive states.
5. Transform data using dbt.
6. Test uniqueness, required fields, accepted values and relationships.
7. Orchestrate the pipeline using Prefect.
8. Create analytical models for roles, locations, languages and skills.
9. Visualise selected results in Power BI.
10. Expose a small set of focused FastAPI endpoints.
11. Answer a narrow set of evidence-grounded questions.
12. Run through Docker Compose.
13. Pass automated checks in GitHub Actions.

This defines the complete local MVP. It is not expected to be implemented during Day 2 and will be developed incrementally.

## Non-goals

The first version will not include:

- Automatic job applications
- Automatic CV rewriting
- Personalised candidate ranking
- Candidate assessment or automated hiring decisions
- Scraping FINN.no, LinkedIn or company websites
- User accounts
- Subscription or payment features
- A large React frontend
- Autonomous multi-agent workflows
- Multiple LLM providers
- Kafka
- Kubernetes
- Multiple cloud platforms
- Salary prediction
- Production-scale infrastructure
- Claims that the dataset represents every Norwegian vacancy

These boundaries protect the project schedule and keep the portfolio focused.

## Technical success measurements

The project will later measure:

- Feed events processed
- Unique advertisements stored
- Advertisements inserted and updated
- Inactive advertisements handled
- Duplicate events detected
- Invalid records rejected
- Successful and failed pipeline runs
- Pipeline execution time
- dbt models created
- dbt tests passed
- API tests passed

## Analytics success measurements

The project will later measure:

- Employers represented
- Locations represented
- Role-family coverage
- Skills identified
- Advertisements with usable location information
- Advertisements with detectable working-language information
- Advertisements with detectable experience-level information

## AI success measurements

The project will later measure:

- Evaluation questions created
- Evidence-supported answers
- Unsupported questions correctly rejected
- Structured responses passing validation
- Retrieval failures
- Response latency
- Approximate model cost where relevant

Target percentages will not be assigned until real source data is available.

## Privacy and responsible use

The source may contain recruiter or contact names, email addresses and telephone numbers. These fields are not required for labour-market analysis.

Personal contact fields will not be included in:

- Analytical models
- Power BI dashboards
- Public API responses
- AI retrieval or generated answers

Inactive advertisements must not be presented as currently open vacancies.

The platform must distinguish among:

- Facts provided directly by the source
- Structured information derived by deterministic transformations
- Information inferred by AI

Unsupported conclusions must be rejected or clearly identified as uncertain.

## Delivery approach

The project will be developed through small, reviewable milestones.

Each milestone should include:

- A focused branch
- Local validation
- A conventional commit
- A pull request
- Successful CI
- A documented checkpoint

The complete local MVP will be stabilised before adding a Microsoft Fabric, Copilot Studio or Power Automate extension.

## Supporting documentation

- Detailed project specification: `docs/project-specification.md`
- Development roadmap: `docs/roadmap.md`
- NAV source notes: `docs/data-source-notes.md`
- Architecture decisions: `docs/decisions.md`
- Milestone checkpoints: `docs/checkpoints/`
