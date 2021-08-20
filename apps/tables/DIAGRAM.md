```mermaid
stateDiagram-v2
    state if_disable <<choice>>
    state if_enable <<choice>>
    state if_review <<choice>>
    state if_pending <<choice>>
    disable: disable new, sync, setup, dashboard

    # stop user adding new data to exceed limit
    [*] --> review_integration
    review_integration --> if_review
    if_review --> ok_review: <100%
    if_review --> enable_after_trial: <100% (connectors)
    if_review --> prevent: >100%

    # check that new sync has exceeded
    [*] --> periodic_row_check
    [*] --> runtime_row_check
    runtime_row_check --> if_disable
    periodic_row_check --> if_disable
    if_disable --> check_ok: <100%
    if_disable --> warning: <110%
    if_disable --> disable: >110%
    disable --> if_enable
    if_enable --> enable_ok: <100%
    if_enable --> do_nothing: >100%

    # delete pending after 14 days
    [*] --> periodic_pending_check
    periodic_pending_check --> if_pending
    if_pending --> ok_pending: <14 days
    if_pending --> delete: >14 days
```
