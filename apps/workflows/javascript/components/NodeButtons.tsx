import React, { useContext } from 'react'
import { getApiClient } from 'apps/base/javascript/api'
import { NodeContext } from '../context'

const client = getApiClient()

export const DeleteButton = ({ id }) => {
  const { removeById } = useContext(NodeContext)
  return (
    <button onClick={() => removeById(id)} title='Delete'>
      <i className='fas fa-fw fa-trash fa-lg'></i>
    </button>
  )
}

const OpenButton = ({ id }) => {
  return (
    <button
      data-action='click->tf-modal#open'
      data-src={`/nodes/${id}`}
      data-item={id}
      title='Edit'
    >
      <i className='fas fa-fw fa-edit fa-lg'></i>
    </button>
  )
}

const DuplicateButton = ({ id }) => {
  const { addNode } = useContext(NodeContext)
  return (
    <button
      onClick={() =>
        client
          .action(window.schema, ['nodes', 'duplicate', 'create'], {
            id,
          })
          .then((res) => addNode(res))
      }
      title='Copy'
    >
      <i className='fas fa-fw fa-copy fa-lg' />
    </button>
  )
}

const NodeButtons = ({ id }) => {
  return (
    <div className='react-flow__buttons'>
      <OpenButton id={id} />
      <DuplicateButton id={id} />
      <DeleteButton id={id} />
    </div>
  )
}

export default NodeButtons
