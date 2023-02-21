import React, { useCallback, useContext } from 'react'
import { isNode, useStoreState, ControlButton } from 'react-flow-renderer'
import { getLayoutedElements } from 'apps/base/javascript/layout'
import { DnDContext, IDnDContext } from '../context'
import { updateWorkflowLayout } from '../api'

const LayoutButton: React.FC = () => {
  const { workflowId, elements, setElements, setNeedsFitView } = useContext(
    DnDContext
  ) as IDnDContext

  const nodes = useStoreState((state) => state.nodes)

  const onLayout = useCallback(() => {
    const layoutedElements = getLayoutedElements(elements, nodes)
    setElements(layoutedElements)

    updateWorkflowLayout(
      workflowId,
      layoutedElements
        .filter(isNode)
        .map((el) => ({ id: el.id, x: el.position.x, y: el.position.y }))
    )

    setNeedsFitView(true)
  }, [elements, nodes])

  return (
    <ControlButton x-tooltip='Arrange automatically' onClick={onLayout}>
      <i className='fas fa-fw fa-sort-size-down'></i>
    </ControlButton>
  )
}

export default LayoutButton
