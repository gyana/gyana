import React, { useContext, useState } from 'react'
import { ElementId, Handle, NodeProps, Position, useStoreState } from 'react-flow-renderer'
import { getApiClient } from 'apps/base/javascript/api'
import NodeButtons, { DeleteButton } from './NodeButtons'
import { DnDContext } from '../context'
import NodeName from './NodeName'
import NodeDescription from './NodeDescription'
import { ErrorIcon, WarningIcon } from './NodeIcons'

const client = getApiClient()

interface Props<T = any> {
  id: ElementId
  data: T
}

const NodeContent: React.FC<Props> = ({ id, data }) => {
  const [, , zoom] = useStoreState((state) => state.transform)
  const showContent = zoom >= 1

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
      <NodeName id={id} name={data.label} />
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
  const { getIncomingNodes } = useContext(DnDContext)
  const incoming = getIncomingNodes(id)

  const showWarning = incoming && incoming[1].length < 1
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
  const { getIncomingNodes } = useContext(DnDContext)
  const incoming = getIncomingNodes(id)

  const showWarning =
    incoming && (data.kind === 'join' ? incoming[1].length != 2 : incoming[1].length == 0)
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
