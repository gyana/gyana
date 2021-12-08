# Schedule

## Data model

- `Job`: the definition of data processing logic with inputs and outputs
  - *Abstract*: Implemented by `sheets.Sheet`, `uploads.Upload`, `connector.Connector`, `workflows.Workflow` and more TBD
- `JobRun`: a single run of a job
  - *Concrete*: `runs.JobRun` - when it started, finished and it's state. The status of a Job is determined by the most recent JobRun.
- `Graph`: a DAG of Job objects - currently a Project in Gyana
- `GraphRun`: a single run of a graph - when it started, finished and it's state. The status of a Graph (i.e. project) is determined by the most recent GraphRun. Each GraphRun is associated with a set of JobRun for the individual jobs.
- `TaskResult`: We use celery tasks to execute our JobRun and GraphRun. This model is provided by django celery results
- `Schedule`: A periodic interval which generates a new GraphRun entity