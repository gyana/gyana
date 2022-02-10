import React from 'react'

interface StatusProps {
  hasBeenRun: boolean
  isOutOfDate: boolean
  errors: {}
}

const Status: React.FC<StatusProps> = ({ hasBeenRun, isOutOfDate, errors }) => (
  <div
    style={{ height: "35px", right: "1.6rem", top: "1.6rem" }}
    className='small flex items-center absolute gap-2 text-black-50'
  >
    {Object.keys(errors).length ? (
      <>
        Workflow has errors
        <i className={`fas fa-fw fa-times-hexagon text-red`}></i>
      </>
    ) : isOutOfDate ? <>
      Workflow is out of date
      <i className={`fas fa-fw fa-exclamation-triangle text-black-50`}></i>
    </> : <>
      Workflow is up to date
      <i className={`fas fa-fw fa-check-circle text-green`}></i>
    </>}
  </div>
)

export default Status
