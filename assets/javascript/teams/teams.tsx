'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import { getApiClient } from '../api'
import TeamApplication from './App'

const domContainer = document.querySelector('#team-content')
const apiUrls = JSON.parse(document.getElementById('api-urls').textContent)

domContainer
  ? ReactDOM.render(
      <TeamApplication client={getApiClient()} urlBase={urlBase} apiUrls={apiUrls} />,
      domContainer
    )
  : null
