```mermaid
stateDiagram-v2
    New: /uploads/new
    Upload: /uploads/id/
    Integration: /integrations/id

    state if_state <<choice>>
    [*] --> New
    New --> if_state
    if_state --> Error: file too large
    if_state --> Error: connection lost
    if_state --> Upload: success
    Error --> New: retry

    state Upload {
        state if_load <<choice>>
        [*] --> Load
        Setup --> Load
        Load --> if_load
        if_load --> RuntimeError: runtime error
        if_load --> Preview: success
        RuntimeError --> Setup
        RuntimeError --> Support
        Preview --> Setup: inferred schema
        Preview --> Approve
        Approve --> [*]
    }

    Upload --> Leave
    Leave --> Upload: navigate back

    Upload --> Delete: manual or 14 days
    Upload --> Integration
    Integration --> [*]
```
