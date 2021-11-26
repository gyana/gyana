import React, { useContext, useState } from 'react'
import {
  Node,
  ElementId,
  getIncomers,
  Handle,
  isNode,
  NodeProps,
  Position,
  useStoreState,
} from 'react-flow-renderer'
import { getApiClient } from 'apps/base/javascript/api'
import NodeButtons, { DeleteButton } from './NodeButtons'
import { DnDContext, IDnDContext } from '../context'
import NodeName from './NodeName'
import NodeDescription from './NodeDescription'
import { ErrorIcon, WarningIcon } from './NodeIcons'

const client = getApiClient()

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
        className={`fas fa-fw ${data.icon}  ${showContent && 'absolute opacity-10'}`}
        data-src={`/nodes/${id}`}
        data-action='dblclick->tf-modal#open'
        data-item={id}
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
      <Handle type='target' position={Position.Left} isConnectable={isConnectable} />
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

  const showWarning = data.kind === 'join' ? incomingCount != 2 : incomingCount == 0
  const warningMessage =
    data.kind === 'join'
      ? 'Join needs two input connections'
      : `${data.label} needs at least one input connection`

  return (
    <>
      {showWarning && <WarningIcon text={warningMessage} />}
      <Handle type='target' position={targetPosition} isConnectable={isConnectable} />
      <NodeContent id={id} data={data} />
      <Handle type='source' position={sourcePosition} isConnectable={isConnectable} />
    </>
  )
}

const TextNode: React.FC<NodeProps> = ({ id, data }: NodeProps) => {
  const [text, setText] = useState(data.text || '')

  const update = () =>
    client.action(window.schema, ['nodes', 'api', 'nodes', 'partial_update'], {
      id,
      text_text: text,
    })

  // TODO: Resizing is broken so it's disabled.
  return (
    <>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={update}
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
