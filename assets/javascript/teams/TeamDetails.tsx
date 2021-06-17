'use strict'
import React, { useState } from 'react'
import { Link, useHistory } from 'react-router-dom'
import { TeamMemberList } from './TeamMembers'
import { InvitationList } from './Invitations'

const TeamDetails = function (props) {
  const [name, setName] = useState(props.team?.name || '')
  const [slug, setSlug] = useState(props.team?.slug || '')
  const [recentlySaved, setRecentlySaved] = useState(false)
  const creatingNewTeam = !Boolean(props.team)
  const canEditTeam = creatingNewTeam ? true : props.team?.is_admin
  const history = useHistory()
  const useRouter = Boolean(props.returnUrl)

  const saveTeam = function (event) {
    props.save(props.team, name, slug)
    setRecentlySaved(true)
    if (useRouter) {
      history.push(props.returnUrl)
    }
    setTimeout(() => setRecentlySaved(false), 3000)
    event.preventDefault()
  }

  const renderIdField = function () {
    if (!creatingNewTeam) {
      return (
        <div className='mb-3'>
          <label className='label form-label'>Team ID</label>
          <input
            className='input form-control'
            type='text'
            placeholder='dunder-mifflin'
            onChange={(event) => setSlug(event.target.value)}
            value={slug}
            disabled={!canEditTeam}
          ></input>
          <p className='help form-text'>A unique ID for your team. No spaces are allowed!</p>
        </div>
      )
    }
  }

  const renderCancel = function () {
    if (useRouter) {
      return (
        <Link to={props.returnUrl}>
          <button className='pg-button-light mx-2'>
            <span>Cancel</span>
          </button>
        </Link>
      )
    } else {
      // when not using the router there's no need for a "cancel" button
      return
    }
  }

  const getSaveButtonText = () => {
    if (recentlySaved) {
      return 'Saved!'
    } else {
      return creatingNewTeam ? 'Add Team' : 'Save Details'
    }
  }
  const renderDetails = function () {
    return (
      <section className='app-card'>
        <form>
          <h3 className='pg-subtitle'>Team Details</h3>
          <div className='mb-3'>
            <label className='label form-label'>Team Name</label>
            <input
              className='input form-control'
              type='text'
              placeholder='Dunder Mifflin'
              onChange={(event) => setName(event.target.value)}
              value={name}
              disabled={!canEditTeam}
            ></input>
            <p className='help form-text'>Your team name.</p>
          </div>

          {renderIdField()}

          {canEditTeam ? (
            <div className='pg-inline-buttons'>
              <button
                className={'button button--filled button--green'}
                onClick={saveTeam}
              >
                <span>{getSaveButtonText()}</span>
              </button>
              {renderCancel()}
            </div>
          ) : (
            ''
          )}
        </form>
      </section>
    )
  }

  const renderMembers = function () {
    if (creatingNewTeam) {
      return null
    } else {
      return <TeamMemberList members={props.team.members} />
    }
  }

  const renderInvitations = function () {
    if (creatingNewTeam) {
      return null
    } else {
      return (
        <InvitationList
          team={props.team}
          client={props.client}
          canManageInvitations={canEditTeam}
          apiUrls={props.apiUrls}
        />
      )
    }
  }

  return (
    <div>
      {renderDetails()}
      {renderMembers()}
      {renderInvitations()}
    </div>
  )
}

export default TeamDetails
