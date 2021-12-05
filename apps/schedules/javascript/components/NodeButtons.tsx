import React from 'react'

const EditButton = ({ id, absoluteUrl }) => {
  return (
    <a href={absoluteUrl} title='Edit'>
      <i className='fas fa-fw fa-edit fa-lg'></i>
    </a>
  )
}

// export const DeleteButton = ({ id }) => {
//   const { deleteNodeById } = useContext(DnDContext) as IDnDContext
//   return (
//     <button onClick={() => deleteNodeById(id)} title='Delete'>
//       <i className='fas fa-fw fa-trash fa-lg'></i>
//     </button>
//   )
// }

// const DuplicateButton = ({ id }) => {
//   const { duplicateNodeById } = useContext(DnDContext) as IDnDContext
//   return (
//     <button onClick={() => duplicateNodeById(id)} title='Copy'>
//       <i className='fas fa-fw fa-copy fa-lg' />
//     </button>
//   )
// }

const NodeButtons = ({ id, absoluteUrl }) => {
  return (
    <div className='react-flow__buttons'>
      <EditButton id={id} absoluteUrl={absoluteUrl} />
      {/* <DuplicateButton id={id} />
      <DeleteButton id={id} /> */}
    </div>
  )
}

export default NodeButtons
