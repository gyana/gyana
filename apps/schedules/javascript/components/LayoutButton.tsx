import { getLayoutedElements } from 'apps/workflows/javascript/layout'
import React, { useEffect, useState } from 'react'
import { Node, Edge, useStoreState, ControlButton, useZoomPanHelper } from 'react-flow-renderer'

interface Props {
  elements: (Edge | Node)[]
  setElements: (elements: (Edge | Node)[]) => void
}

const LayoutButton: React.FC<Props> = ({ elements, setElements }) => {
  const nodes = useStoreState((state) => state.nodes)
  const { fitView } = useZoomPanHelper()
  const [shouldLayout, setShouldLayout] = useState(true)

  // https://github.com/wbkd/react-flow/issues/1353
  useEffect(() => {
    if (shouldLayout && nodes.length > 0 && nodes.every((el) => el.__rf.width && el.__rf.height)) {
      const layoutedElements = getLayoutedElements(elements, nodes)
      setElements(layoutedElements)
      fitView()
      setShouldLayout(false)
    }
  }, [shouldLayout, nodes])

  const onLayout = () => setShouldLayout(true)

  return (
    <ControlButton data-controller='tooltip' onClick={onLayout}>
      <i className='fas fa-fw fa-sort-size-down'></i>
      <template data-tooltip-target='body'>Format</template>
    </ControlButton>
  )
}

export default LayoutButton
