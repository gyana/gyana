- Create GCP project
- Create BigQuery instance
- Create public and private storage buckets
- Create service account with (potentially less permissive but needs read and write)
  - BigQuery Admin
  - Storage Admin
- Download service account credentials json
- Point `GCP_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS`, `GCP_BQ_SVC_ACCOUNT`,
  `GS_BUCKET_NAME`, `GS_PUBLIC_BUCKET_NAME` to right variables
