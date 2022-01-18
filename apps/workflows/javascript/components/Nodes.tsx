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
import { updateNode } from '../api'

interface Props<T = any> {
  id: ElementId
  data: T
}

const useGetIncomingCount = (id: string) => {
  const { elements } = useContext(DnDContext) as IDnDContext
  const targetElement = elements.find((el) => isNode(el) && el.id === id)
  return targetElement ? getIncomers(targetElement, elements).length : 0
}

const NodeContent: React.FC<Props> = ({ id, data }) => {
  const [, , zoom] = useStoreState((state) => state.transform)
  const showContent = zoom >= 1.2

  return (
    <>
      {data.error && <ErrorIcon text={data.error} />}
      <NodeButtons id={id} />
      <i
        className={`fas fa-fw ${data.icon} ${showContent && 'absolute opacity-10'}`}
        data-modal-src={`/nodes/${id}`}
        data-action='dblclick->tf-modal#open'
        data-modal-item={id}
        data-modal-id='workflow-modal'
        data-modal-classes='tf-modal--full'
      ></i>
      {showContent && (
        <div className='p-2'>
          <NodeDescription id={id} data={data} />
        </div>
      )}
      <NodeName id={id} name={data.label} kind={data.kind} />
    </>
  )
}

const InputNode: React.FC<NodeProps> = ({ id, data, isConnectable }) => (
  <>
    <NodeContent id={id} data={data} />
    <Handle type='source' position={Position.Right} isConnectable={isConnectable} />
  </>
)

const OutputNode: React.FC<NodeProps> = ({ id, data, isConnectable }) => {
  const incomingCount = useGetIncomingCount(id)
  const showWarning = incomingCount == 0
  return (
    <>
      {showWarning && <WarningIcon text='Save Data needs one input connection' />}
      <NodeContent id={id} data={data} />
      <Handle type='target' position={Position.Left} id='0' isConnectable={isConnectable} />
    </>
  )
}

const DefaultNode: React.FC<NodeProps> = ({
  id,
  data,
  isConnectable,
  targetPosition = Position.Left,
  sourcePosition = Position.Right,
}) => {
  const incomingCount = useGetIncomingCount(id)
  const updateNodeInternals = useUpdateNodeInternals()

  const showWarning = data.kind === 'join' ? incomingCount != 2 : incomingCount == 0
  const warningMessage =
    data.kind === 'join'
      ? 'Join needs two input connections'
      : `${data.label} needs at least one input connection`

  const maxParents = NODES[data.kind].maxParents
  const handles = maxParents === -1 ? incomingCount + 1 : maxParents

  useEffect(() => {
    updateNodeInternals(id)
  }, [id, incomingCount])

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
          style={{ top: `${Math.round((100 * (idx + 1)) / (handles + 1))}%`, borderRadius: 0 }}
        />
      ))}
      <NodeContent id={id} data={data} />
      <Handle type='source' position={sourcePosition} isConnectable={isConnectable} />
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
