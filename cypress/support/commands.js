// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

const TEST_EMAIL = 'test@gyana.com'
const TEST_PASSWORD = 'seewhatmatters'

const login = (email = TEST_EMAIL, password = TEST_PASSWORD) => {
  // https://github.com/cypress-io/cypress-example-recipes/tree/master/examples/logging-in__csrf-tokens
  cy.request('/accounts/login/')
    .its('body')
    .then((body) => {
      const $html = Cypress.$(body)
      const csrfmiddlewaretoken = $html.find('input[name=csrfmiddlewaretoken]').val()

      cy.request({
        method: 'POST',
        url: '/accounts/login/',
        failOnStatusCode: false,
        form: true,
        body: {
          login: email,
          password,
          csrfmiddlewaretoken,
        },
      }).then((resp) => {
        expect(resp.status).to.eq(200)
      })
    })
}

Cypress.Commands.add('login', login)
