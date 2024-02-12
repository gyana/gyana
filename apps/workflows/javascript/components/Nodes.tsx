import React, { useContext, useEffect, useState } from 'react'
import {
  ElementId,
  getIncomers,
  Handle,
  isNode,
  NodeProps,
  Position,
  useStoreState,
  useUpdateNodeInternals,
} from 'react-flow-renderer'
import NodeButtons, { DeleteButton } from './NodeButtons'
import { DnDContext, IDnDContext } from '../context'
import NodeName from './NodeName'
import NodeDescription from './NodeDescription'
import { ErrorIcon, WarningIcon } from './NodeIcons'
import { NODES } from '../interfaces'
import { getNode, toNode, updateNode } from '../api'
import { GyanaEvents } from 'apps/base/javascript/events'

interface Props<T = any> {
  id: ElementId
  data: T
  showFilledIcon?: Boolean
}

const useGetIncomingCount = (id: string) => {
  const { elements } = useContext(DnDContext) as IDnDContext
  const targetElement = elements.find((el) => isNode(el) && el.id === id)
  return targetElement ? getIncomers(targetElement, elements).length : 0
}

const NodeContent: React.FC<Props> = ({ id, data, showFilledIcon = true }) => {
  const [, , zoom] = useStoreState((state) => state.transform)
  const showContent = zoom >= 1.2

  return (
    <>
      {data.error && <ErrorIcon text={data.error} />}
      <NodeButtons id={id} />
      <i
        className={`
          ${showFilledIcon ? 'fas' : 'fal opacity-80'}
          fa-fw
          ${data.icon}
          ${showContent && 'absolute opacity-10'}`}
        {...{ 'x-modal:dblclick.full.persist': `/nodes/${id}` }}
      ></i>
      <div className={`p-2 ${!showContent && 'hidden'}`}>
        <NodeDescription id={id} data={data} />
      </div>
      <NodeName
        id={id}
        placeholder={data.tableName || NODES[data.kind].displayName}
        name={data.label}
        kind={data.kind}
      />
    </>
  )
}

const InputNode: React.FC<NodeProps> = ({
  id,
  data: initialData,
  isConnectable,
}) => {
  const [data, setData] = useState(initialData)
  const onNodeConfigUpdate = async () => {
    const result = await getNode(id)
    setData(toNode(result).data)
  }

  useEffect(() => {
    const eventName = `${GyanaEvents.UPDATE_NODE}-${id}`
    window.addEventListener(eventName, onNodeConfigUpdate, false)
    return () => window.removeEventListener(eventName, onNodeConfigUpdate)
  }, [])

  return (
    <>
      <NodeContent id={id} data={data} showFilledIcon={!!data.tableName} />
      <Handle
        type='source'
        position={Position.Right}
        isConnectable={isConnectable}
      />
    </>
  )
}

const OutputNode: React.FC<NodeProps> = ({ id, data, isConnectable }) => {
  const incomingCount = useGetIncomingCount(id)
  const showWarning = incomingCount == 0

  return (
    <>
      {showWarning && (
        <WarningIcon text='Save Data needs one input connection' />
      )}
      <NodeContent id={id} data={data} showFilledIcon={!showWarning} />
      <Handle
        type='target'
        position={Position.Left}
        id='0'
        isConnectable={isConnectable}
      />
    </>
  )
}

const DefaultNode: React.FC<NodeProps> = ({
  id,
  data: initialData,
  isConnectable,
  targetPosition = Position.Left,
  sourcePosition = Position.Right,
}) => {
  const incomingCount = useGetIncomingCount(id)
  const updateNodeInternals = useUpdateNodeInternals()
  const [data, setData] = useState(initialData)

  const showWarning =
    data.kind === 'join' ? !data.join_is_valid : incomingCount == 0
  const warningMessage =
    data.kind === 'join'
      ? 'Join needs at least two input connections and correct join conditions'
      : `${data.label} needs at least one input connection`

  const maxParents = NODES[data.kind].maxParents
  const handles = maxParents === -1 ? incomingCount + 1 : maxParents

  useEffect(() => {
    updateNodeInternals(id)
  }, [id, incomingCount])

  const onNodeUpdate = async () => {
    const result = await getNode(id)
    setData(toNode(result).data)
  }

  useEffect(() => {
    const eventName = `${GyanaEvents.UPDATE_NODE}-${id}`
    window.addEventListener(eventName, onNodeUpdate, false)
    return () => window.removeEventListener(eventName, onNodeUpdate)
  }, [])

  return (
    <>
      {showWarning && <WarningIcon text={warningMessage} />}
      {Array.from(Array(handles), (x, idx) => (
        <Handle
          key={idx}
          type='target'
          position={targetPosition}
          isConnectable={isConnectable}
          id={idx.toString()}
          style={{
            top: `${Math.round((100 * (idx + 1)) / (handles + 1))}%`,
            borderRadius: 0,
          }}
        />
      ))}
      <NodeContent id={id} data={data} showFilledIcon={!showWarning} />
      <Handle
        type='source'
        position={sourcePosition}
        isConnectable={isConnectable}
      />
    </>
  )
}

const TextNode: React.FC<NodeProps> = ({ id, data }: NodeProps) => {
  const [text, setText] = useState(data.text || '')

  // TODO: Resizing is broken so it's disabled.
  return (
    <>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={() => updateNode(id, { text_text: text })}
        placeholder={'Leave a note to annotate the workflow...'}
        style={{ resize: 'none', borderRadius: '10px' }}
      />

      <div className='react-flow__buttons'>
        <DeleteButton id={id} />
      </div>
    </>
  )
}

const defaultNodeTypes = {
  input: InputNode,
  output: OutputNode,
  default: DefaultNode,
  text: TextNode,
}

export default defaultNodeTypes
