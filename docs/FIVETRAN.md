# Fivetran

Sharing obtained knowledge from the past months working with Fivetran.

## **Adding new connectors**

The following two steps allow for easy adding of a connector

### **Create connector config in `services.yaml`**

New connectors can be added in [services.yaml](../apps/connectors/services.yaml). All the Fivetran connectors can be found in the [Fivetran API](https://fivetran.com/docs/rest-api/connectors/config). The `service` key in the fivetran docs is the key in `services.yaml`.

The `services.yaml` spec is as follows:

> **`name`** - display name in the web app.

> **`color`** - hex color value for the web app.

> **`internal`** - flag that hides the connector in production when set to `t`.

> **`requires_schema_prefix`** - is supposed to set to `t` when the Fivetran docs have the `schema_prefix` required for a connector. For example for database connectors Fivetran needs a schema prefix to work with the database schema and tables within that schema.

> **`category`** - category name of the category this connector should be grouped by.

> **`static_config`** - are key-value pairs that are sent as the `config` body in the Fivetran API request. Some connectors need hardcoded static config to work. This key solves that.

### **Add icon for the connector**

We look up the **`svg`** icons located in `static/images/integrations/fivetran/*.svg` for the connector. The key in `services.yaml` should be the same as the icon file name. Make sure that the icon that is added is an `.svg` file.

## **FivetranClient**

The FivetranClient class (found in [fivetran.py](../apps/connectors/fivetran.py)) is becoming the interface between Gyana and Fivetran. Here is where most of the Fivetran communication happens.

### **Integration creation flow**

There's heavy usage of tasks here. I did this to get the loading steps in `_flow.html` to give a nice progress flow. Instead of waiting for each of the tasks to finish we respond quick and defer the longer tasks to celery. The frontend then pings celery to listen for completion. This same logic can be rewritten using Django Channels, might be nicer and more modern! Django Channels allow to push the task progress to the client, instead of having the client ping the server for changes. Utilizing websockets for this kind of communication is a much more modern way of web dev.

1. The moment a user selects a Fivetran integration we call to `FivetranClient.authorize` is done. This creates the card and sends the authenticated URL to the client.
2. The user sets up their connector using the [Fivetran Connect Card](https://fivetran.com/docs/rest-api/connectors/connect-card). Note that the connector is paused the moment it's created to allow the user to select the schema to sync later on in step 4.
3. The user is redirected to `authorize_fivetran_redirect` in `apps/integrations/views.py` which starts polling the created connector in a Celery task (`apps/integrations/tasks.py:poll_fivetran_historical_sync`).
4. While the polling in the background happens the user is redirected to `apps/integrations/views.py:IntegrationSetup` where the user gets to select the schema, if there is one. The Google Sheets Fivetran connector for example doesn't have a schema, most others do.
5. When the schema has been selected by the user we start the `apps/integrations/tasks.py:update_integration_fivetran_schema` task that we listen to in `_flow.html`. Once the schema update task finishes the user is sent to the last step.
6. `apps/integrations/views.py:start_fivetran_integration` finally starts the `apps/integrations/tasks.py:start_fivetran_integration_task` task and after completion the user is sent to the integration.

The access to connector data and Table creation is discussed in **Fivetran - BigQuery - Gyana**

## **Fivetran - BigQuery - Gyana**

We use BQ as our destination for all Fivetran's synced data. Fivetran owns and maintains the synced data in our BQ instances. We get the data from those tables through the `fivetran_id` (this is the internal ID Fivetran creates for its connectors) and `schema` (is the schema name in BQ, generated in `FivetranClient.create`) fields on the Integration model.

We create `Table`s that point to the BQ tables created by Fivetran. The function that does this is `apps/integrations/bigquery.py:get_tables_in_dataset`. This function is executed the moment the historical sync is done (`apps/integrations/tasks.py:poll_fivetran_historical_sync`).

## **Fivetran webapp**

The Fivetran webapp is a bit clunky, but offers some decent tools for management of connectors.

- All connectors can be find in either `bigquery_mvp` (for local dev and Heroku mvp build) or `bigquery_beta` (for Heroku beta build) destinations.
- We can manually adjust settings for users having problems with their connectors.
- Logs on a connector can be helpful for debugging (understanding why a connector failed to sync for example)
- The `schema` tab on a connector is virtually the same as the `schema` tab in Gyana. We literally pull the same data in. Important note here is that some schemas have required tables that cannot be deselected/unsynced. Those are **hidden** from the `schema` in Gyana to avoid confusion.
- Usage of our **MAR** (Monthly Active Rows) in Fivetran can be found [here](https://fivetran.com/account/usage). The page will list any connector in all our destinations, also including current/old product.
