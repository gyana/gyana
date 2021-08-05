export function getApiClient() {
  // this method will only work if you have also done the prerequisite steps on the page
  // more details here: https://www.django-rest-framework.org/topics/api-clients/#javascript-client-library
  const auth = new coreapi.auth.SessionAuthentication({
    csrfCookieName: 'csrftoken',
    csrfHeaderName: 'X-CSRFToken',
  })
  return new coreapi.Client({ auth })
}

export const Api = {
  getApiClient,
}
