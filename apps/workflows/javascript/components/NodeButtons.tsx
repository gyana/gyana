import React, { useContext } from 'react'
import { DnDContext, IDnDContext } from '../context'

const EditButton = ({ id }) => {
  const params = new URLSearchParams(window.location.search);
  const model_item = params.get("modal_item");

  return (
    <button
      data-action='click->tf-modal#open'
      title='Edit'
      data-modal-id='workflow-modal'
      data-modal-src={`/nodes/${id}`}
      data-modal-item={id}
      data-modal-classes='tf-modal--full'
      data-tf-modal-target={model_item == id ? 'onParam' : ''}
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
