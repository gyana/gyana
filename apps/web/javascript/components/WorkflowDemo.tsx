import { getLayoutedElements } from 'apps/base/javascript/layout'
import React, { useEffect, useMemo, useRef, useState } from 'react'

import ReactFlow, { isEdge, useStoreState, useZoomPanHelper } from 'react-flow-renderer'
import { useDemoStore } from '../store'

import initialElements, { getInputNodeLabel } from './workflow-demo-elements'

const NODES = JSON.parse(
  (document.getElementById('nodes') as HTMLScriptElement).textContent as string
)

const useLayout = (ref, elements, setElements) => {
  const nodes = useStoreState((state) => state.nodes)
  const { fitView } = useZoomPanHelper()
  const [shouldLayout, setShouldLayout] = useState(true)
  const [hasLayout, setHasLayout] = useState(false)

  const observer = useMemo(() => new ResizeObserver((entries) => setHasLayout(true)), [])

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
      if (isEdge(el)) {
        el.sourcePosition = 'right'
        el.targetPosition = 'left'
      }
      return el
    })
  )

  const [{ integrations, node }, setDemoStore] = useDemoStore(() =>
    setElements((els) =>
      els.map((el) => {
        if (el.id === '1') el.data = { label: getInputNodeLabel(0) }
        if (el.id === '2') el.data = { label: getInputNodeLabel(1) }
        return el
      })
    )
  )

  const selectNode = (node) => {
    setElements((els) =>
      els.map((el) => {
        if (el.id === '4') {
          el.type = 'default'
          el.data = {
            label: (
              <div className='relative w-full h-full flex items-center justify-center'>
                <div>
                  <i className={`fa ${node.icon} fa-8x`}></i>
                </div>
                <div className='absolute -bottom-12 left-0 right-0 text-2xl font-semibold text-gray-600'>
                  {node.displayName}
                </div>
              </div>
            ),
          }
        }
        if (isEdge(el)) {
          el.animated = true
          el.style = { strokeWidth: 10, stroke: '#e6e6e6', strokeDasharray: '35 5' }
        }
        return el
      })
    )
  }

  useLayout(ref, elements, setElements)

  return (
    <>
      <div ref={ref} className='h-80 w-full relative card card--none overflow-hidden'>
        <ReactFlow
          elements={elements}
          nodesConnectable={false}
          zoomOnScroll={false}
          panOnScroll={false}
        />
      </div>
      <div className='mt-4 card card--none'>
        <div className='pad w-full grid grid-cols-10 divide-x divide-y'>
          {Object.values(NODES).map((item) => (
            <button
              key={item.icon}
              className={`p-2 focus:outline-none ${node?.icon === item.icon
                ? 'text-white bg-indigo-600 hover:bg-indigo-700'
                : 'text-gray-600 hover:text-gray-900'
                }`}
              onClick={() => {
                setDemoStore({ integrations, node: item })
                selectNode(item)
              }}
            >
              <i className={`fa ${item.icon} fa-lg`}></i>
            </button>
          ))}
          {/* empty div */}
          <div></div>
        </div>
      </div>
    </>
  )
}

export default WorkflowDemo
