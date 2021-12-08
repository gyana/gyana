# Schedule

Inspired by projects like Airflow, Dagster and Prefect.

## Data model

- `Job`: the definition of data processing logic with inputs and outputs
  - *Abstract*: Implemented by `sheets.Sheet`, `uploads.Upload`, `connector.Connector`, `workflows.Workflow` and more TBD
- `JobRun`: a single run of a `Job`
  - *Concrete*: Implemented by `runs.JobRun` with `started_at`, `completed_at` and `state` = `PENDING, RUNNING, FAILED, SUCCESS`
- `Graph`: a DAG of `Job` objects
  - *Abstract*: Implemented by `projects.Project`
- `GraphRun`: a single run of a `Graph`
  - *Concrete*: Implemented by `runs.GraphRun` (NYI)
- `Task`: The execution of a `JobRun` or `GraphRun` as a celery task
  - *Concrete*: Implemented by `django_celery_results.TaskResult`
- `Schedule`: A periodic interval which generates and executes a new `GraphRun`
  - *Conrete*: Implemented by `schedules.Schedule` (NYI), plus `django_celery_beat` models

## Computed properties

We are using Django signals and save method overrides to automatically compute state properties.

- The state of an individual `JobRun` or a `GraphRun` is computed from the celery `TaskResult`
- The state of a `JobRun` within a `GraphRun` is manually computed with a single execution, rather than launching individual celery tasks per `JobRun`
- The state of a `Job` is computed by the most recent `JobRun`
- The state of a `Project` is computed by the most recent `GraphRun`

*Note that we need special logic for connectors, as they do not run in celery tasks*

## Examples

To run an individual sheets sync:
- Create a `JobRun` object and trigger the "run sheet sync" celery task with the `task_id`
- When the celery task is completed, it creates a new `TaskResult` with `SUCCESS` state
- The `JobRun` state is updated to `SUCCESS` via signal
- The sheet `Integration` state is updated to `DONE`

To run the entire project graph:
- Create a `GraphRun` object and trigger the "run project graph" celery task with the `task_id`
- The task manually creates the individual `JobRun` entities, iterates through in dependency order, and update the `started_at`, `completed_at` and `state` properties
- Updates to these properties will cascade through to the parent entities via signals
- When the celery task is completed, it creates a new `TaskResult` with `SUCCESS` state
- The `GraphRun` state is updated to `SUCCESS` via signal
- The `Project` state is updated to `SUCCESS`