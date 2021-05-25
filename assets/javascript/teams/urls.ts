// note: these must match what's set by the django template.
// see `api_url_helpers.py` for an example
const TEAM_PLACEHOLDER = '__team_slug__'
const INVITATION_PLACEHOLDER = '__invite_id__'

export const getInviteUrl = function (urlTemplate, teamSlug, inviteId) {
  return getTeamUrl(urlTemplate, teamSlug).replace(INVITATION_PLACEHOLDER, inviteId)
}

export const getTeamUrl = function (urlTemplate, teamSlug) {
  return urlTemplate.replace(TEAM_PLACEHOLDER, teamSlug)
}
