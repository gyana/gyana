import { getAction } from '../api'

const API_PREFIX = ['teams', 'api']
const SINGLE_TEAM_API_PREFIX = ['a', 'team', 'api']

export function getAPIAction(action) {
  return getAction(API_PREFIX, action)
}

function getSingleTeamAPIAction(action) {
  return getAction(SINGLE_TEAM_API_PREFIX, action)
}

export function getCreateInvitationAPIAction() {
  return getSingleTeamAPIAction(['invitations', 'create'])
}

export function getDeleteInvitationAPIAction() {
  return getSingleTeamAPIAction(['invitations', 'delete'])
}
