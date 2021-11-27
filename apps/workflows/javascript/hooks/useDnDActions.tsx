import {
  addEdge,
  removeElements,
  updateEdge as updateEdgeElements,
  isNode,
  Edge,
  Node,
  OnLoadParams,
  Connection,
  getIncomers,
} from 'react-flow-renderer'

import '../styles/_dnd-flow.scss'
import { createEdge, createNode, deleteEdge, deleteNode, moveNode, updateEdge } from '../actions'
import { RefObject, useState } from 'react'
import { NODES } from '../interfaces'

type Element = Node | Edge

const canAddEdge = (elements: Element[], target: string) => {
  const targetElement = elements.find((el) => isNode(el) && el.id === target) as Node
  if (targetElement) {
    const incomingNodes = getIncomers(targetElement, elements)

    // Node arity is defined in nodes/bigquery.py
    // Join (2), Union/Except/Insert (-1 = Inf), otherwise (1)
    const maxParents = NODES[targetElement.data.kind].maxParents

    if (maxParents === -1 || incomingNodes.length < maxParents) {
      return true
    } else {
      // TODO: Add notification here
      // alert("You can't add any more incoming edges to this node")
      return false
    }
  }
}

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

  const onConnect = async (connection: Connection) => {
    if (canAddEdge(elements, connection.target)) {
      const edge = await createEdge(connection)
      setElementsDirty((els) => addEdge(edge, els))
    }
  }

  const onEdgeUpdate = (oldEdge: Edge, newConnection: Connection) => {
    const { source, target } = newConnection

    if (target !== null && source !== null) {
      // need to check the arity of a target element
      if (oldEdge.target === target || canAddEdge(elements, target)) {
        updateEdge(oldEdge, newConnection)
        setElementsDirty((els) => updateEdgeElements(oldEdge, newConnection, els))
      }
    }
  }

  const onElementsRemove = (elementsToRemove: Element[]) => {
    setElementsDirty((els) => removeElements(elementsToRemove, els))
    elementsToRemove.forEach((el) => {
      if (isNode(el)) {
        deleteNode(el)
      } else {
        deleteEdge(el)
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
