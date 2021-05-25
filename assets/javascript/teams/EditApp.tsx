'use strict'
import React, { useState } from 'react'
import { getAPIAction } from './api'
import TeamDetails from './TeamDetails'

const EditTeamApplication = function (props) {
  const [team, setTeam] = useState(props.team)

  const saveTeam = function (team, name, slug) {
    const params = {
      id: team.id,
      name: name,
      slug: slug,
    }
    const action = getAPIAction(['teams', 'partial_update'])
    props.client.action(window.schema, action, params).then((result) => {
      const slugChanged = team.slug !== result.slug
      if (slugChanged) {
        // todo: do a full page redirect since we need to bust all team links on the page
      } else {
        setTeam(result)
      }
    })
  }

  return (
    <TeamDetails
      save={saveTeam}
      returnUrl={null}
      team={team}
      client={props.client}
      apiUrls={props.apiUrls}
    />
  )
}

export default EditTeamApplication
