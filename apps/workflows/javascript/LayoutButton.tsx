import React, { useCallback } from 'react'
import { isNode, useStoreState, ControlButton, Edge, Node } from 'react-flow-renderer'
import { getApiClient } from 'apps/base/javascript/api'
import { getLayoutedElements } from './layout'

const client = getApiClient()

interface Props {
  elements: (Node | Edge)[]
  setElements: (elements: (Node | Edge)[]) => void
  setViewHasChanged
  workflowId: string
}

const LayoutButton: React.FC<Props> = ({
  elements,
  setElements,
  setViewHasChanged,
  workflowId,
}) => {
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
    setViewHasChanged(true)
  }, [elements, nodes])

  return (
    <ControlButton data-controller='tooltip' onClick={onLayout}>
      <i title='Format workflow' className='fas fa-fw fa-sort-size-down'></i>
      <template data-tooltip-target='body'>Format</template>
    </ControlButton>
  )
}

export default LayoutButton
