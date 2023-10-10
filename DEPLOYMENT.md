# Deployment

We're running a traditional Django app on [Heroku](https://dashboard.heroku.com/pipelines/33c2c23a-3f74-49ca-b19a-e3203445c2d2) with dev/staging/prod deployments.

## Release

- Choose and merge a commit from main onto the release branch
- Run and fix the automated [QA process](DEVELOPMENT.md#QA) (Cypress test suite)
- Push any fixes onto main and cherrypick to the release branch
- Run the manual QA process (written test plan) on gyana-release
- Document and push any further fixes onto the release branch
- If downtime is expected, communiate to users and switch Heroku to maintenance mode
- Manual deploy release branch to gyana-beta
- Manual smoke test on gyana-beta
- If there is an issue, see [rollback](#Rollbacks)

## Rollbacks

Heroku has automated [rollbacks](https://blog.heroku.com/releases-and-rollbacks),
but you'll need to manually migrate the Django database to its historical state.

Remember to switch Heroku to maintenance mode and run this SQL script to generate
app/migration pairs for the downgrade:

```sql
with changed_apps as (
	select distinct app
	from django_migrations
	where applied > '202X-XX-XX XX:XX:XX'
),
rollback_migrations as (
	select *
	from django_migrations
	where applied < '202X-XX-XX XX:XX:XX'
)
select app
	, name
from (
	select a.app
		, coalesce(m.name, 'zero') as name
		, rank() over (partition by a.app order by applied desc) as rank
	from rollback_migrations m
	right join changed_apps a
		on m.app = a.app
) X
where rank = 1
order by app
;
```

You can rollback the apps one by one (in future it would be good to
[automate](https://stackoverflow.com/questions/60411090/run-reverse-django-migration-on-heroku-after-release-failure) this):

```bash
heroku run --app gyana-beta python manage.py migrate <app> <name>
```

You can get the timestamp from the release metadata you plan to rollback to. Remember
to add a buffer of ~10 mins since the migrations run after a release:

```bash
heroku releases --app gyana-beta
```

Finally, rollback the app to the chosen version. It has to happen in this order,
since the migrations will not exist when you rollback the code:

```bash
heroku rollback <version> --app gyana-beta
```

## Services

With links for the production app:

- Deployments, logs, metrics: [Heroku](https://dashboard.heroku.com/apps/gyana-beta)
- Exception, uptime and cron monitoring: [Honeybadger](https://app.honeybadger.io/projects/88968/faults)
- Traces: [Honeycomb](https://ui.honeycomb.io/gyanav2)
- Analytics: [Google Analytics](https://analytics.google.com/analytics/web/#/p284522086/reports/reportinghub)
- Events: [Segment](https://app.segment.com/gyana-beta/overview)
- Support: [Intercom](https://app.intercom.com)
- Emails: [SendGrid](https://app.sendgrid.com/)

## Setup

The app runs on Heroku, GCP, with GoDaddy for DNS.

### Heroku

We setup the app in the Heroku UI, key points to note:

- Region: EU
- Add-ons: Heroku Postgres and Heroku Redis
- Dynos for web, beat and worker (should happen automatically)
- Buildpacks:
  - Node: `heroku/nodejs`
  - Python: `heroku/python`
  - GCP authentication: `https://github.com/buyersight/heroku-google-application-credentials-buildpack.git`

Heroku config variables, with production examples:

```bash
DJANGO_SETTINGS_MODULE = gyana.settings.heroku
ENVIRONMENT = production
EXTERNAL_URL = https://app.gyana.com
GCP_BQ_SVC_ACCOUNT = gyana-app@gyana-app-314217.iam.gserviceaccount.com
GCP_PROJECT = gyana-app-314217
GOOGLE_APPLICATION_CREDENTIALS = google-credentials.json
GOOGLE_CREDENTIALS = {{ credential_json_from_svc_account }}
GS_BUCKET_NAME = gyana-app
HASHIDS_SALT = {{ django.utils.crypto.get_random_string(32) }}
HELLONEXT_SSO_TOKEN = {{ hellonext_sso_token }}
HEROKU_API_KEY = {{ heroku authorizations:create }}
HEROKU_APP = gyana-beta
HONEYBADGER_API_KEY = {{ honeybadger_api_key }}
HONEYCOMB_API_KEY = {{ honeycomb_api_key }}
SECRET_KEY = {{ secret_key }} # generate online
SEGMENT_ANALYTICS_JS_WRITE_KEY = {{ segment_js_secret }}
SEGMENT_ANALYTICS_WRITE_KEY = {{ segment_py_secret }}
SENDGRID_API_KEY = {{ sendgrid_api_secret }}
```

The database and redis config variable are generated automatically by the add-ons.
For redis, you'll need to add `?ssl_cert_reqs=none`.

Remember to add [Honeybadger support](https://docs.honeybadger.io/guides/heroku/)
for Heroku errors and deployments.

### GCP

The MVP/release and production environments run in separate environments, within
the `gyana.co.uk` organisation. Key points to note:

- Enable APIs:
  - [Google sheets](https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com)
  - [Google Drive](https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com)
- All developer emails added in IAM with the following roles:
  - `Cloud KMS Admin`
  - `Cloud KMS CryptoKey Encrypter/Decrypter`
  - `Editor`
- A service account which:
  - Has its email is set to the `GCP_BQ_SVC_ACCOUNT` env variable
  - Has `BigQuery Admin` role in IAM
  - Has `Storage Admin` role in IAM

You'll need to create a bucket in Cloud Storage (`gyana-app` in production). As
users can upload CSV files directly to the bucket, we need to set the CORS rules:

```bash
gsutil cors set {CORS_JSON_LOCATION} gs://gyana-app
```

With the following JSON (edit as necessary):

```json
[
  {
    "origin": ["https://beta.gyana.com"], // Or whichever origin the app is run on
    "responseHeader": ["Content-Type", "x-goog-resumable"],
    "method": ["PUT", "POST"],
    "maxAgeSeconds": 3600
  }
]
```

### Custom domain

- Add the custom domain `app.gyana.com` to the Heroku settings page
- Add the wildcard `*.gyana.com` SSL cert from LastPass (.key and .pem files)
- Setup GoDaddy:
  - `Host`: `beta`
  - `Points to`: `<DNS_TARGET from Heroku settings>`
  - `TLS`: `600s`
