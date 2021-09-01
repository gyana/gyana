# Fivetran

Sharing obtained knowledge from the past months working with Fivetran.

## Overview

We have two destinations, `bigquery_beta` for production and `bigquery_mvp` for everything else.

- Connector API docs - https://fivetran.com/docs/rest-api/connectors
- Overview dashboard - https://fivetran.com/dashboard
- Usage dashboard - https://fivetran.com/account/usage

## Configuration

You can automatically download the configuration from all connectors from the
[retrieve source metadata](https://fivetran.com/docs/rest-api/connectors#retrievesourcemetadata) endpoint.

> TODO: Implement this!

We have an internal configuration in `services.yaml` with the following extra information:

- `internal`: if true, only show for superusers
- `requires_schema_prefix`: only true for database connectors, e.g. Postgres
- `static_config`: extra configuration settings that need to be appended to a creation request
- `reports`: hard-coded set of reports for certain connectors, e.g. Google Analytics

## Implementation

The `apps.connectors.fivetran.FivetranClient` is a wrapper for the Fivetran API,
with a mock implementation that is helpful for local development and testing (since
the initial sync for a connectors can be long).

Fivetran syncs the data to a pre-determined schema in our BigQuery instance. The user
can decide which tables are synced, and manually trigger a re-sync.

At one level, we are reproducing parts of their dashboard wrapped in our UI, although
there are a couple of critical missing features that block feature parity:

- webhooks for sync completion events
- real-time logs are only available on the Enterprise tier

## Debugging

With the Fivetran dashboard, we can manually adjust settings for users having
problems issues and view logs to debug failing connectors.

## Fivetran Roadmap for Q4 2021

Jimmy Hooker (PM for powered-by-Fivetran) has shared this roadmap:

- Connect Card Links: Think Stripe Payment Links but for Connect Cards
- White Labeling Connect Cards: Custom logo and colors for Connect Cards
- Connect Card Design: Reworking Connect Card design for maximum onboarding ease
- Configurable Connect Cards: Allow things like ‘select only one account’ from marketing style connectors
- End-to-End Embed: Handle full Fivetran experience through a seamless, configurable UI. Connector Choosing, Connector Auth (via Connect Cards), and Connector State.
- API Completeness: Bring the API more in line with what’s possible from the dashboard, like selecting accounts, reports, and connector configuration through the API
- Next Gen Docs: Next gen developer experience focused on rapid onboarding
- API Versioning: Implement versioning in our API so that we can release breaking changes more easily while ensuring customer ease of use.
- SDKs: Per-language SDKs to make interacting with the API easier
