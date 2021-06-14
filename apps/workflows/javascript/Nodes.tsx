import React, { createContext, useContext, useState, useEffect } from 'react'
import { Handle, NodeProps, Position, Node } from 'react-flow-renderer'

export const NodeContext = createContext({
  removeById: (id: string) => {},
  client: null,
  getIncomingNodes: (id: string): [Node, Node[]] | null => null,
})

const DeleteButton = ({ id }) => {
  const { removeById } = useContext(NodeContext)
  return (
    <button onClick={() => removeById(id)}>
      <i className='fas fa-trash fa-lg'></i>
    </button>
  )
}

const OpenButton = ({ id }) => {
  const workflowId = window.location.pathname.split('/')[4]

  return (
    <button data-action='click->tf-modal#open'>
      <i data-src={`/workflows/${workflowId}/nodes/${id}`} className='fas fa-edit fa-lg'></i>
    </button>
  )
}

const Description = ({ id, data }) => {
  const { client } = useContext(NodeContext)
  const workflowId = window.location.pathname.split('/')[4]

  const [description, setDescription] = useState()

  const onNodeConfigUpdate = async () => {
    const result = await client.action(window.schema, ['workflows', 'api', 'nodes', 'read'], {
      workflow: workflowId,
      id,
    })

    setDescription(result.description)
  }

  useEffect(() => {
    const eventName = `node-updated-${id}`
    window.addEventListener(eventName, onNodeConfigUpdate, false)
    return () => window.removeEventListener(eventName, onNodeConfigUpdate)
  }, [])

  return (
    <p
      title={description || data.description}
      className='max-w-full overflow-hidden whitespace-pre overflow-ellipsis'
    >
      {description || data.description}
    </p>
  )
}

const Buttons = ({ id }) => {
  return (
    <div className='react-flow__buttons'>
      <OpenButton id={id} />
      <DeleteButton id={id} />
    </div>
  )
}

const ErrorIcon = ({ text }) => (
  <div
    title={text}
    className='flex items-center justify-around absolute -top-2 -right-2 bg-red-10 rounded-full w-6 h-6 text-red'
  >
    <i className='fad fa-bug '></i>
  </div>
)

const WarningIcon = ({ text }) => (
  <div
    className='flex items-center justify-around absolute -top-2 -left-2 rounded-full w-6 h-6 text-orange cursor-pointer'
    title={text}
  >
    <i className='fas fa-exclamation-triangle bg-white'></i>
  </div>
)

const InputNode = ({ id, data, isConnectable, selected }: NodeProps) => (
  <>
    <Buttons id={id} />
    {data.error && <ErrorIcon text={data.error} />}

    <i className={`fas fa-fw ${data.icon}`}></i>
    <h4 className='capitalize'>{data.label}</h4>

    {/* <Description id={id} data={data} /> */}

    <Handle type='source' position={Position.Right} isConnectable={isConnectable} />
  </>
)

const OutputNode = ({ id, data, isConnectable, selected }: NodeProps) => {
  const { getIncomingNodes } = useContext(NodeContext)
  const incoming = getIncomingNodes(id)

  const showWarning = incoming && incoming[1].length < 1
  return (
    <>
      <Buttons id={id} />
      {data.error && <ErrorIcon text={data.error} />}
      {showWarning && <WarningIcon text='Output needs to be connected!' />}
      <Handle type='target' position={Position.Left} isConnectable={isConnectable} />

      <i className={`fas fa-fw ${data.icon}`}></i>
      <h4 className='capitalize'>{data.label}</h4>
      {/* <Description id={id} data={data} /> */}
    </>
  )
}

const DefaultNode = ({
  id,
  data,
  isConnectable,
  targetPosition = Position.Left,
  sourcePosition = Position.Right,
}: NodeProps) => {
  const { getIncomingNodes } = useContext(NodeContext)
  const incoming = getIncomingNodes(id)

  const showWarning =
    incoming && (data.label === 'join' ? incoming[1].length != 2 : incoming[1].length == 0)

  return (
    <>
      <Buttons id={id} />
      {data.error && <ErrorIcon text={data.error} />}
      {showWarning && <WarningIcon text={`${data.label} node needs to be connected to a node`} />}
      <Handle type='target' position={targetPosition} isConnectable={isConnectable} />

      <i className={`fas fa-fw ${data.icon}`}></i>
      <h4 className='capitalize'>{data.label}</h4>

      <Handle type='source' position={sourcePosition} isConnectable={isConnectable} />
    </>
  )
}

const TextNode = ({ id, data, selected }: NodeProps) => {
  const [text, setText] = useState(data.text || '')
  const { client } = useContext(NodeContext)

  const update = () =>
    client.action(window.schema, ['workflows', 'api', 'nodes', 'partial_update'], {
      id,
      text_text: text,
    })

  return (
    <>
      <textarea value={text} onChange={(e) => setText(e.target.value)} onBlur={update} />
      <DeleteButton id={id} />
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
