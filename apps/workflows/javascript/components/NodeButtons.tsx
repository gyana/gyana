import React, { useContext } from 'react'
import { DnDContext, IDnDContext } from '../context'

const EditButton = ({ id }) => {
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

export const DeleteButton = ({ id }) => {
  const { deleteNodeById } = useContext(DnDContext) as IDnDContext
  return (
    <button onClick={() => deleteNodeById(id)} title='Delete'>
      <i className='fas fa-fw fa-trash fa-lg'></i>
    </button>
  )
}

const DuplicateButton = ({ id }) => {
  const { duplicateNodeById } = useContext(DnDContext) as IDnDContext
  return (
    <button onClick={() => duplicateNodeById(id)} title='Copy'>
      <i className='fas fa-fw fa-copy fa-lg' />
    </button>
  )
}

const NodeButtons = ({ id }) => {
  return (
    <div className='react-flow__buttons'>
      <EditButton id={id} />
      <DuplicateButton id={id} />
      <DeleteButton id={id} />
    </div>
  )
}

export default NodeButtons
