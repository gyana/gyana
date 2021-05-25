'use strict'
import React from 'react'
import ReactDOM from 'react-dom'
import { getApiClient } from '../api'
import EditTeamApplication from './EditApp'

const domContainer = document.querySelector('#manage-team-content')

const team = JSON.parse(document.getElementById('team').textContent)
const apiUrls = JSON.parse(document.getElementById('api-urls').textContent)

domContainer
  ? ReactDOM.render(
      <EditTeamApplication client={getApiClient()} team={team} apiUrls={apiUrls} />,
      domContainer
    )
  : null
