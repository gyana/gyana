In order to self-host Gyana, you need a [Google Cloud Platform](https://cloud.google.com/) account. To get started they offer some [free credits](https://cloud.google.com/pricing).

Once you have signed up follow these steps:

- Create a [GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- Create a BigQuery instance
- Create [public and private storage buckets](https://cloud.google.com/storage/docs/creating-buckets)
- Create a [service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts) with (potentially less permissive but needs read and write)
  - BigQuery Admin
  - Storage Admin
- [Download service account credentials JSON](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating)
- Point `ENGINE_URL`, `GOOGLE_APPLICATION_CREDENTIALS`, `GCP_BQ_SVC_ACCOUNT`,
  `GS_BUCKET_NAME`, `GS_PUBLIC_BUCKET_NAME` to right variables
