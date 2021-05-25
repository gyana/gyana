'use strict'
import React from 'react'

const TeamMemberTableRow = function (props) {
  return (
    <tr>
      <td>{props.display_name}</td>
      <td>{props.role}</td>
    </tr>
  )
}

export const TeamMemberList = function (props) {
  return (
    <section className='app-card'>
      <h3 className='pg-subtitle'>Team Members</h3>
      <table className='table is-striped is-fullwidth'>
        <thead>
          <tr>
            <th>Member</th>
            <th>Role</th>
          </tr>
        </thead>
        <tbody>
          {props.members.map((membership, index) => {
            return <TeamMemberTableRow key={membership.id} index={index} {...membership} />
          })}
        </tbody>
      </table>

      {}
    </section>
  )
}
