import React from 'react'
import { NODES } from '../interfaces'

const ZeroState: React.FC = () => (
  <div className='placeholder-scr placeholder-scr--fillscreen gap-10'>
    <div className='flex items-center max-w-lg gap-7'>
      <i className={`fas fa-fw ${NODES['input'].icon} text-green fa-2x`}></i>
      <p>
        Start building your workflow by dragging in a <strong>Get data</strong> node
      </p>
    </div>

    <div className='flex items-center max-w-lg gap-7'>
      <i className={`fas fa-fw ${NODES['filter'].icon} text-blue fa-2x`}></i>
      <p>
        Drag and connect other <strong>Transformation</strong> nodes to clean and filter your data
      </p>
    </div>

    <div className='flex items-center max-w-lg gap-7'>
      <i className={`fas fa-fw ${NODES['output'].icon} text-pink fa-2x`}></i>
      <p>
        Once you are happy with your results, drag in a <strong>Save Data</strong> node and name it
      </p>
    </div>

    <div className='flex items-center max-w-lg gap-7'>
      <i className={`fas fa-fw fa-play-circle text-green fa-2x`}></i>
      <p>
        Press <strong>Run</strong> in the top right to create the new data source
      </p>
    </div>
  </div>
)

export default ZeroState
