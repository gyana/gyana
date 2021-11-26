import {
  addEdge,
  removeElements,
  updateEdge,
  isNode,
  Edge,
  Node,
  OnLoadParams,
} from 'react-flow-renderer'

import '../styles/_dnd-flow.scss'
import { createNode, deleteNode, moveNode, updateParentEdges } from '../actions'
import {
  addEdgeToParents,
  canAddEdge,
  removeEdgeFromParents,
  updateEdgeSourceInParents,
  updateEdgeTargetInParents,
} from '../edges'
import { RefObject, useState } from 'react'

type Element = Node | Edge

const useDnDActions = (
  workflowId: number,
  reactFlowWrapper: RefObject<HTMLDivElement>,
  elements: Element[],
  setElementsDirty
) => {
  const [reactFlowInstance, setReactFlowInstance] = useState<OnLoadParams>()

  const onLoad = (instance) => setReactFlowInstance(instance)

  const onDragOver = (event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }

  const onDrop = async (event: DragEvent) => {
    event.preventDefault()
    const { dataTransfer, clientX, clientY } = event

    if (
      reactFlowWrapper.current !== null &&
      reactFlowInstance !== undefined &&
      dataTransfer !== null
    ) {
      const type = dataTransfer.getData('application/reactflow')
      const { left, top } = reactFlowWrapper.current.getBoundingClientRect()
      const position = reactFlowInstance.project({
        x: clientX - left,
        y: clientY - top,
      })
      const newNode = await createNode(workflowId, type, position)
      setElementsDirty((es) => es.concat(newNode))
    }
  }

  const onNodeDragStop = (event, node) => moveNode(node)

  const onConnect = (params) => {
    if (canAddEdge(elements, params.target)) {
      updateParentEdges(params.target, addEdgeToParents(elements, params.source, params.target))
      setElementsDirty((els) =>
        addEdge({ ...params, arrowHeadType: 'arrowclosed', type: 'smoothstep' }, els)
      )
    }
  }

  const onEdgeUpdate = (oldEdge: Edge, newEdge: Edge) => {
    // Update the target of the edge
    if (oldEdge.source === newEdge.source) {
      if (canAddEdge(elements, newEdge.target)) {
        const [oldParents, newParents] = updateEdgeTargetInParents(elements, oldEdge, newEdge)
        updateParentEdges(oldEdge.target, oldParents)
        updateParentEdges(newEdge.target, newParents)
        setElementsDirty((els) => updateEdge(oldEdge, newEdge, els))
      }
    }
    // Update the source of the edge
    else {
      updateParentEdges(newEdge.target, updateEdgeSourceInParents(elements, oldEdge, newEdge))
      setElementsDirty((els) => updateEdge(oldEdge, newEdge, els))
    }
  }

  const onElementsRemove = (elementsToRemove) => {
    setElementsDirty((els) => removeElements(elementsToRemove, els))
    elementsToRemove.forEach((el) => {
      if (isNode(el)) {
        deleteNode(el)
      } else {
        updateParentEdges(el.target, removeEdgeFromParents(elements, el))
      }
    })
  }

  return {
    onLoad,
    onDragOver,
    onDrop,
    onNodeDragStop,
    onConnect,
    onEdgeUpdate,
    onElementsRemove,
  }
}

export default useDnDActions
