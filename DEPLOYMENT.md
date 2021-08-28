# https://beta.gyana.com

## How to deploy

The [Deploy](https://dashboard.heroku.com/apps/gyana-beta/deploy/github) page on the Heroku gyana-beta app has a `Manual deploy` where we can select a branch and deploy it. For now only use the `main` branch for deploys!

## How to rollback

As described in [Heroku: Releases and Rollbacks](https://blog.heroku.com/releases-and-rollbacks) it's easy to rollback a broken release using the following commands

```zsh
# Rolls back to the previous successful release
heroku rollback --app gyana-beta
# Rolls back to the specified <version> e.g. v42
heroku rollback <version> --app gyana-beta
# To see all versions run
heroku releases --app gyana-beta
```

## Setup

Below describes the steps to create this deployment from scratch

### Google Cloud Platform

---

Created a separate project within the `gyana.co.uk` company called `Gyana App`

Important attributes within this project:

- [Google sheets API enabled](https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com)
- All developer emails added in IAM with the following roles:
  - `Cloud KMS Admin`
  - `Cloud KMS CryptoKey Encrypter/Decrypter`
  - `Editor`
- A service account which:
  - Has its email is set to the `GCP_BQ_SVC_ACCOUNT` env variable
  - Has `BigQuery Admin` role in IAM
  - Has `Storage Admin` role in IAM

#### **Cloud Storage**

Create a bucket in Cloud Storage named `gyana-app`

Set the right CORS rules on the buckets for uploads (UPLOADS WILL NOT WORK WITHOUT THIS):

- To set the cors json `gsutil cors set {CORS_JSON_LOCATION} gs://vayu-datasets-{ENV}`
- The `gyana-app` bucket requires the following CORS rules

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

### Heroku

---

A [gyana-beta](https://dashboard.heroku.com/apps/gyana-beta) has been created using the following commands.

```zsh
# Using --remote here to add a remote to the local git config
heroku create --region=eu --remote beta --addons=heroku-postgresql,heroku-redis
```

#### **Buildpacks**

In the [Settings](https://dashboard.heroku.com/apps/gyana-beta/settings) page add the following Buildpacks in the order listed:

- `heroku/nodejs`
- `heroku/python`
- `https://github.com/buyersight/heroku-google-application-credentials-buildpack.git`

#### **Custom domain**

On the Heroku settings page a custom domain `beta.gyana.com` is added. To get the wildcard `*.gyana.com` SSL working the .key en .pem file from LastPass are uploaded into the Heroku system. This SSL combo will then be used for that domain. Heroku also generates a `DNS Target` that will be used for the GoDaddy step below.

#### **Env variables that matter**

These config variables are set in the [Settings](https://dashboard.heroku.com/apps/gyana-beta/settings) tab in the Heroku web app

- `DJANGO_SETTINGS_MODULE` = `gyana.settings.heroku`
- `GOOGLE_APPLICATION_CREDENTIALS` = `google-credentials.json`
- `GOOGLE_CREDENTIALS` = `<credential_json_from_svc_account>`
- `SECRET_KEY` = `<secret_key_val>`
- `GCP_PROJECT` = `gyana-app-314217`
- `GCP_BQ_SVC_ACCOUNT` = `gyana-app@gyana-app-314217.iam.gserviceaccount.com`
- `EXTERNAL_URL` = `https://app.gyana.com`
- `CLOUD_NAMESPACE` = `heroku`
- `GS_BUCKET_NAME` = `gyana-app`
- `FIVETRAN_KEY` = `<api_key_for_fivetran>`
- _Only for beta deployment_ `FIVETRAN_GROUP` = `intended_monsieur`
- `SENDGRID_API_KEY` = `<sendgrid_api_secret>`
- `SEGMENT_ANALYTICS_JS_WRITE_KEY` = `<segment_js_secret>`
- `SEGMENT_ANALYTICS_WRITE_KEY` = `<segment_py_secret>`
- `HASHIDS_SALT` = `<django.utils.crypto.get_random_string(32)>`

#### **Deploy**

Setup the `gyana/gyana` git repository in the [Deploy settings](https://dashboard.heroku.com/apps/gyana-beta/deploy/github). At the bottom of the page manual deploys can be executed when needed.

### GoDaddy

---

To setup the DNS created in the Heroku settings we need to add a CNAME record with:

- `Host`: `beta`
- `Points to`: `<DNS_TARGET from Heroku settings>`
- `TLS`: `600s`
