import {
  addEdge,
  removeElements,
  updateEdge,
  isNode,
  Edge,
  Node,
  OnLoadParams,
  Connection,
  ArrowHeadType,
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

  const onDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }

  const onDrop = async (event: React.DragEvent<HTMLDivElement>) => {
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

  const onNodeDragStop = (event: React.DragEvent<HTMLDivElement>, node: Node) => moveNode(node)

  const onConnect = (connection: Edge) => {
    if (canAddEdge(elements, connection.target)) {
      updateParentEdges(
        connection.target,
        addEdgeToParents(elements, connection.source, connection.target)
      )
      setElementsDirty((els) =>
        addEdge(
          { ...connection, arrowHeadType: ArrowHeadType.ArrowClosed, type: 'smoothstep' },
          els
        )
      )
    }
  }

  const onEdgeUpdate = (oldEdge: Edge, newConnection: Connection) => {
    const { source, target } = newConnection

    if (target !== null && source !== null) {
      // Update the target of the edge
      if (oldEdge.source === source) {
        if (canAddEdge(elements, target)) {
          const [oldParents, newParents] = updateEdgeTargetInParents(
            elements,
            oldEdge,
            source,
            target
          )
          updateParentEdges(oldEdge.target, oldParents)
          updateParentEdges(target, newParents)
          setElementsDirty((els) => updateEdge(oldEdge, newConnection, els))
        }
      }
      // Update the source of the edge
      else {
        updateParentEdges(target, updateEdgeSourceInParents(elements, oldEdge))
        setElementsDirty((els) => updateEdge(oldEdge, newConnection, els))
      }
    }
  }

  const onElementsRemove = (elementsToRemove: Element[]) => {
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
