import React, { createContext, useContext, useState, useEffect } from 'react'
import { Handle, NodeProps, Position } from 'react-flow-renderer'

export const NodeContext = createContext({
  removeById: (id: string) => {},
  client: null,
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

const InputNode = ({ id, data, isConnectable, selected }: NodeProps) => (
  <>
    {selected && <Buttons id={id} />}
    {data.error && <ErrorIcon text={data.error} />}
    <h4 className='capitalize'>{data.label}</h4>
    <Description id={id} data={data} />

    <Handle type='source' position={Position.Right} isConnectable={isConnectable} />
  </>
)

const OutputNode = ({ id, data, isConnectable, selected }: NodeProps) => (
  <>
    {selected && <Buttons id={id} />}
    {data.error && <ErrorIcon text={data.error} />}
    <Handle type='target' position={Position.Left} isConnectable={isConnectable} />

    <h4 className='capitalize'>{data.label}</h4>
    <Description id={id} data={data} />
  </>
)

const DefaultNode = ({
  id,
  data,
  isConnectable,
  targetPosition = Position.Left,
  sourcePosition = Position.Right,
  selected,
}: NodeProps) => {
  return (
    <>
      {selected && <Buttons id={id} />}
      {data.error && <ErrorIcon text={data.error} />}
      <Handle type='target' position={targetPosition} isConnectable={isConnectable} />

      <h4 className='capitalize'>{data.label}</h4>
      <Description id={id} data={data} />

      <Handle type='source' position={sourcePosition} isConnectable={isConnectable} />
    </>
  )
}

const defaultNodeTypes = {
  input: InputNode,
  output: OutputNode,
  default: DefaultNode,
}

export default defaultNodeTypes
