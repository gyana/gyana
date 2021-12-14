import { getLayoutedElements } from 'apps/base/javascript/layout'
import React, { useEffect, useState } from 'react'
import { Node, Edge, useStoreState, ControlButton, useZoomPanHelper } from 'react-flow-renderer'

interface Props {
  elements: (Edge | Node)[]
  setElements: React.Dispatch<React.SetStateAction<(Edge | Node)[]>>
}

const LayoutButton: React.FC<Props> = ({ elements, setElements }) => {
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

  const onLayout = () => setShouldLayout(true)

  return (
    <ControlButton data-controller='tooltip' onClick={onLayout}>
      <i className='fas fa-fw fa-sort-size-down'></i>
      <template data-tooltip-target='body'>Format</template>
    </ControlButton>
  )
}

export default LayoutButton
