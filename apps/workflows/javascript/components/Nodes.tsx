import React, { useContext, useState } from 'react'
import { Handle, NodeProps, Position, useStoreState } from 'react-flow-renderer'
import { getApiClient } from 'apps/base/javascript/api'
import NodeButtons, { DeleteButton } from './NodeButtons'
import { NodeContext } from '../context'
import NodeName from './NodeName'
import NodeDescription from './NodeDescription'
import { ErrorIcon, WarningIcon } from './NodeIcons'

const client = getApiClient()

const InputNode: React.FC<NodeProps> = ({ id, data, isConnectable }) => {
  const [, , zoom] = useStoreState((state) => state.transform)
  const showContent = zoom >= 1.8

  return (
    <>
      <NodeButtons id={id} />
      {data.error && <ErrorIcon text={data.error} />}
      <NodeName id={id} name={data.label} />

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

      <Handle type='source' position={Position.Right} isConnectable={isConnectable} />
    </>
  )
}

const OutputNode: React.FC<NodeProps> = ({ id, data, isConnectable }) => {
  const [, , zoom] = useStoreState((state) => state.transform)
  const showContent = zoom >= 1.8

  const { getIncomingNodes } = useContext(NodeContext)
  const incoming = getIncomingNodes(id)

  const showWarning = incoming && incoming[1].length < 1
  return (
    <>
      <NodeButtons id={id} />
      {data.error && <ErrorIcon text={data.error} />}
      {showWarning && <WarningIcon text='Output needs to be connected!' />}
      <Handle type='target' position={Position.Left} isConnectable={isConnectable} />

      <i
        data-action='dblclick->tf-modal#open'
        data-src={`/nodes/${id}`}
        data-item={id}
        className={`fas fa-fw ${data.icon} ${showContent && 'absolute opacity-10'}`}
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

const DefaultNode: React.FC<NodeProps> = ({
  id,
  data,
  isConnectable,
  targetPosition = Position.Left,
  sourcePosition = Position.Right,
}) => {
  const [, , zoom] = useStoreState((state) => state.transform)
  const showContent = zoom >= 1.8

  const { getIncomingNodes } = useContext(NodeContext)
  const incoming = getIncomingNodes(id)

  const showWarning =
    incoming && (data.kind === 'join' ? incoming[1].length != 2 : incoming[1].length == 0)
  const warningMessage =
    data.kind === 'join'
      ? 'Join node requires two input nodes'
      : `${data.label} node needs at least one input node`

  return (
    <>
      <NodeButtons id={id} />
      {data.error && <ErrorIcon text={data.error} />}
      {showWarning && <WarningIcon text={warningMessage} />}
      <Handle type='target' position={targetPosition} isConnectable={isConnectable} />

      <i
        data-action='dblclick->tf-modal#open'
        data-src={`/nodes/${id}`}
        data-item={id}
        className={`fas fa-fw ${data.icon} ${showContent && 'absolute opacity-10'}`}
      ></i>
      {showContent && <NodeDescription id={id} data={data} />}

      <NodeName id={id} name={data.label} />

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
