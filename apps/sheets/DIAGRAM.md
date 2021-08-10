```mermaid
stateDiagram-v2
    New: /sheets/new
    Sheet: /sheets/id/
    Integration: /integrations/id

    state if_state <<choice>>
    [*] --> New
    New --> if_state
    if_state --> Error: invalid URL
    if_state --> Error: cannot access
    if_state --> Error: invalid cell range
    if_state --> Sheet: success
    Error --> New: retry

    state Sheet {
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

    Sheet --> Leave
    Leave --> Sheet: navigate back

    Sheet --> Delete: manual or 14 days
    Sheet --> Integration
    Integration --> [*]
    Integration --> Sheet: resync
```
