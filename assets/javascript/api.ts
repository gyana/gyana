export function getAction(apiRoot, action) {
  // DRF dynamically sets the apiRoot based on the common shared prefix, so we attempt
  // to inspect window.schema for the action - first searching for the namespaced version,
  // then trying the action directly
  let namespacedAction = apiRoot.concat(action)
  if (!window.schema) {
    console.error('window.schema not found. Did you forget to load your schemajs?')
  } else if (pathExistsInObject(action, window.schema.content)) {
    return action
  } else if (pathExistsInObject(namespacedAction, window.schema.content)) {
    return namespacedAction
  } else {
    // fall back to default, even though it may not be valid
    console.error(
      'action ' + namespacedAction + 'not found in API schema. Some functionality may not work.'
    )
  }
  return apiRoot.concat(action)
}

export function getApiClient() {
  // this method will only work if you have also done the prerequisite steps on the page
  // more details here: https://www.django-rest-framework.org/topics/api-clients/#javascript-client-library
  const auth = new coreapi.auth.SessionAuthentication({
    csrfCookieName: 'csrftoken',
    csrfHeaderName: 'X-CSRFToken',
  })
  return new coreapi.Client({ auth })
}

function pathExistsInObject(path, schema) {
  let currentSchema = schema
  for (let pathPart of path) {
    if (currentSchema) {
      currentSchema = currentSchema[pathPart]
    } else {
      return false
    }
  }
  return Boolean(currentSchema)
}

export const Api = {
  getAction,
  getApiClient,
}
