import React, { useCallback, useContext } from 'react'
import { isNode, useStoreState, ControlButton } from 'react-flow-renderer'
import { getApiClient } from 'apps/base/javascript/api'
import { getLayoutedElements } from '../layout'
import { DnDContext, IDnDContext } from '../context'

const client = getApiClient()

const LayoutButton: React.FC = () => {
  const { workflowId, elements, setElements, setNeedsFitView } = useContext(
    DnDContext
  ) as IDnDContext

  const nodes = useStoreState((state) => state.nodes)

  const onLayout = useCallback(() => {
    const layoutedElements = getLayoutedElements(elements, nodes)
    setElements(layoutedElements)

    client.action(window.schema, ['workflows', 'update_positions', 'create'], {
      id: workflowId,
      nodes: layoutedElements
        .filter(isNode)
        .map((el) => ({ id: el.id, x: el.position.x, y: el.position.y })),
    })
    setNeedsFitView(true)
  }, [elements, nodes])

  return (
    <ControlButton data-controller='tooltip' onClick={onLayout}>
      <i className='fas fa-fw fa-sort-size-down'></i>
      <template data-tooltip-target='body'>Format</template>
    </ControlButton>
  )
}

export default LayoutButton
