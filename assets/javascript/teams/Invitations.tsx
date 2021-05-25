'use strict'
import React, { useState } from 'react'
import { Cookies } from '../app'
import { getCreateInvitationAPIAction, getDeleteInvitationAPIAction } from './api'
import { getInviteUrl } from './urls'

const InviteWidget = function (props) {
  const [email, setEmail] = useState('')

  const sendInvite = function () {
    let action = getCreateInvitationAPIAction()
    let params = {
      team: props.team.id,
      team_slug: props.team.slug,
      email: email,
    }
    props.client.action(window.schema, action, params).then((result) => {
      props.addInvitation(result)
      setEmail('')
    })
  }

  return (
    <div>
      <h3 className='pg-subtitle'>Invite Team Members</h3>
      <div className='field'>
        <input
          className='input form-control'
          type='email'
          placeholder='michael@dundermifflin.com'
          onChange={(event) => setEmail(event.target.value)}
          value={email}
        ></input>
        <a className='pg-button-secondary mt-2' onClick={() => sendInvite()}>
          <span className='icon is-small'>
            <i className='fa fa-envelope-o'></i>
          </span>
          <span>Invite</span>
        </a>
      </div>
    </div>
  )
}

const InvitationTableRow = function (props) {
  const controls = props.canManageInvitations ? (
    <div className='pg-inline-buttons pg-justify-content-end'>
      <a className='pg-button-secondary' onClick={() => props.resendInvitation(props.index)}>
        <span>{props.sent ? 'Sent!' : 'Resend Invitation'}</span>
      </a>
      <a className='pg-button-secondary mx-2' onClick={() => props.delete(props.index)}>
        <span>Cancel Invitation</span>
      </a>
    </div>
  ) : (
    ''
  )
  return (
    <tr>
      <td>{props.email}</td>
      <td>{props.role}</td>
      <td>{controls}</td>
    </tr>
  )
}

export const InvitationList = function (props) {
  const [invitations, _setInvitations] = useState(props.team.invitations)

  const setInvitations = function (newInvitations) {
    // have to copy the invitations array because state comparisons are shallow
    // https://stackoverflow.com/a/59690997/8207
    _setInvitations([...newInvitations])
  }

  const addInvitation = function (invitation) {
    invitations.push(invitation)
    setInvitations(invitations)
  }

  const deleteInvitation = function (index) {
    const action = getDeleteInvitationAPIAction()
    const params = {
      id: invitations[index].id,
      team_slug: props.team.slug,
    }
    props.client.action(window.schema, action, params).then((result) => {
      invitations.splice(index, 1)
      setInvitations(invitations)
    })
  }

  const resendInvitation = function (index) {
    const inviteUrl = getInviteUrl(
      props.apiUrls['single_team:resend_invitation'],
      props.team.slug,
      invitations[index].id
    )
    fetch(inviteUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': Cookies.get('csrftoken'),
      },
    }).then((response) => {
      if (response.ok) {
        invitations[index].sent = true
        setInvitations(invitations)
      }
    })
  }

  const renderPendingInvitations = function () {
    if (invitations.length === 0) {
      return (
        <p className='my-2 has-text-grey text-muted'>
          Any pending invitations will show up here until accepted.
        </p>
      )
    }
    return (
      <div>
        <br />
        <h3 className='pg-subtitle'>Pending Invitations</h3>
        <table className='table pg-table'>
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {invitations.map((invitation, index) => {
              return (
                <InvitationTableRow
                  key={invitation.id}
                  index={index}
                  {...invitation}
                  delete={(index) => deleteInvitation(index)}
                  resendInvitation={(index) => resendInvitation(index)}
                  canManageInvitations={props.canManageInvitations}
                />
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <section className='app-card'>
      {props.canManageInvitations ? (
        <InviteWidget team={props.team} client={props.client} addInvitation={addInvitation} />
      ) : (
        ''
      )}
      {renderPendingInvitations()}
    </section>
  )
}
