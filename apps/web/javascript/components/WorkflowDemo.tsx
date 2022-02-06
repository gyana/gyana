import { getLayoutedElements } from 'apps/base/javascript/layout'
import React, { useEffect, useMemo, useRef, useState } from 'react'

import ReactFlow, { Background, useStoreState, useZoomPanHelper } from 'react-flow-renderer'

import initialElements from './initial-elements'

const useLayout = (ref, elements, setElements) => {
  const nodes = useStoreState((state) => state.nodes)
  const { fitView } = useZoomPanHelper()
  const [shouldLayout, setShouldLayout] = useState(true)
  const [hasLayout, setHasLayout] = useState(false)

  const observer = useMemo(
    () =>
      new ResizeObserver((entries) => {
        console.log('LAYOUT')
        setHasLayout(true)
      }),
    []
  )

  useEffect(() => {
    if (observer && ref.current) {
      observer.observe(ref.current)
      return () => observer.disconnect()
    }
  }, [ref.current, observer])

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
  const ref = useRef()
  const [elements, setElements] = useState(
    initialElements.map((el) => {
      if (!el?.source) {
        el.sourcePosition = 'right'
        el.targetPosition = 'left'
      }
      return el
    })
  )

  useLayout(ref, elements, setElements)

  return (
    <div ref={ref} className='reactflow-wrapper h-full w-full border-gray'>
      <ReactFlow
        elements={elements}
        nodesConnectable={false}
        zoomOnScroll={false}
        panOnScroll={false}
      />
    </div>
  )
}

export default WorkflowDemo
