import React from 'react'

interface Props {
  error: string
}

const ErrorState: React.FC<Props> = ({ error }) => (
  <div className='placeholder-scr placeholder-scr--fillscreen'>
    <i className='fa fa-exclamation-triangle text-red fa-4x mb-3'></i>
    <p>{error}</p>
    <p>
      Contact{' '}
      <a className='link' href='mailto: support@gyana.com'>
        support@gyana.com
      </a>{' '}
      for support.
    </p>
    <p>
      Or try reloading{' '}
      <button onClick={() => window.location.reload()}>
        <i className='far fa-sync text-blue'></i>
      </button>
    </p>
  </div>
)

export default ErrorState
