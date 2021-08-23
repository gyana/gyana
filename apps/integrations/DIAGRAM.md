```mermaid
stateDiagram-v2
    New: /integration/new
    Integration: /integration/id
    Exit: /integrations/id

    state if_state <<choice>>
    [*] --> New
    New --> if_state
    if_state --> Error: failed to start
    if_state --> Integration: success
    Error --> New: retry

    state Integration {
        state if_load <<choice>>
        [*] --> Load
        [*] --> Setup: databases
        Setup --> Load
        Load --> if_load
        if_load --> RuntimeError: runtime error
        if_load --> Preview: success
        RuntimeError --> Load: retry
        RuntimeError --> Setup: configure
        RuntimeError --> Support
        Preview --> Setup: inferred schema
        Preview --> Approve
        Approve --> [*]
    }

    Integration --> Leave
    Leave --> Integration: navigate back

    Integration --> Delete: manual or 14 days
    Integration --> Exit
    Exit --> [*]
    Exit --> Integration: (connector, sheet) resync

```

If tables are de-selected in setup stage after initial sync, manually delete in BigQuery.

Error states:

- upload: file too large, connection lost
- connector: authorization failed
- sheet: invalid URL, cannot access, invalid cell range
