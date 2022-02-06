import { getLayoutedElements } from 'apps/base/javascript/layout'
import React, { useEffect, useState } from 'react'

import ReactFlow, { Background, useStoreState, useZoomPanHelper } from 'react-flow-renderer'

import initialElements from './initial-elements'

const onLoad = (reactFlowInstance) => {
  reactFlowInstance.fitView()
}

const useLayout = (elements, setElements) => {
  const nodes = useStoreState((state) => state.nodes)
  const { fitView } = useZoomPanHelper()
  const [shouldLayout, setShouldLayout] = useState(true)
  const [hasLayout, setHasLayout] = useState(false)

  // https://github.com/wbkd/react-flow/issues/1353
  useEffect(() => {
    if (shouldLayout && nodes.length > 0 && nodes.every((el) => el.__rf.width && el.__rf.height)) {
      const layoutedElements = getLayoutedElements(elements, nodes)
      setElements(layoutedElements)
      setHasLayout(true)
      setShouldLayout(false)
    }
  }, [shouldLayout, nodes])

  // wait for layout to update and only then fit view
  useEffect(() => {
    if (hasLayout) {
      fitView()
      setHasLayout(false)
    }
  }, [hasLayout])
}

const WorkflowDemo = () => {
  const [elements, setElements] = useState(
    initialElements.map((el) => {
      if (!el?.source) {
        el.sourcePosition = 'right'
        el.targetPosition = 'left'
      }
      return el
    })
  )

  useLayout(elements, setElements)

  return (
    <ReactFlow
      elements={elements}
      onLoad={onLoad}
      snapToGrid={true}
      snapGrid={[15, 15]}
      nodesConnectable={false}
      zoomOnScroll={false}
      panOnScroll={false}
      defaultZoom={100}
    >
      <Background color='#aaa' gap={16} />
    </ReactFlow>
  )
}

export default WorkflowDemo
