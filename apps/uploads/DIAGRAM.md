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

    state Upload {
        state if_load <<choice>>
        [*] --> Setup
        Setup --> Load
        Load --> if_load
        if_load --> RuntimeError: runtime error
        if_load --> Preview: success
        Preview --> Setup
        Preview --> Approve
        Approve --> [*]
    }

    Upload --> Integration
    Integration --> [*]
```
