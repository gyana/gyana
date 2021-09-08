// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

import 'cypress-file-upload'

const TEST_EMAIL = 'test@gyana.com'
const TEST_PASSWORD = 'seewhatmatters'

const login = (email = TEST_EMAIL, password = TEST_PASSWORD) => {
  // https://github.com/cypress-io/cypress-example-recipes/tree/master/examples/logging-in__csrf-tokens
  cy.request('/login/')
    .its('body')
    .then((body) => {
      const $html = Cypress.$(body)
      const csrfmiddlewaretoken = $html.find('input[name=csrfmiddlewaretoken]').val()

      cy.request({
        method: 'POST',
        url: '/login/',
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

const logout = () => {
  cy.request('/logout').then((resp) => {
    expect(resp.status).to.eq(200)
  })
}

Cypress.Commands.add('logout', logout)

const outbox = () => cy.request('/cypress/outbox').then((response) => response.body)

Cypress.Commands.add('outbox', outbox)

const periodic = () => cy.request('/cypress/periodic').then((response) => response.body)

Cypress.Commands.add('periodic', periodic)

const dataTransfer = new DataTransfer()

Cypress.Commands.add('drag', (selector) => {
  return cy.get(selector).trigger('dragstart', { dataTransfer }).trigger('drag', { dataTransfer })
})

Cypress.Commands.add('drop', (selector) => {
  return cy.get(selector).trigger('drop', { dataTransfer })
})

// https://github.com/wbkd/react-flow/blob/main/cypress/support/commands.js
Cypress.Commands.add('reactFlowDrag', (objId, { x, y }) => {
  return cy
    .get(`[data-id=${objId}]`)
    .trigger('mousedown', { which: 1 })
    .trigger('mousemove', { clientX: x, clientY: y })
    .trigger('mouseup', { force: true })
})

Cypress.Commands.add('connectNodes', (source, target) => {
  cy.get(`[data-id=${source}]`)
    .find('.react-flow__handle.source')
    .trigger('mousedown', { which: 1 })

  cy.get(`[data-id=${target}]`)
    .find('.react-flow__handle.target')
    .trigger('mousemove', { dataTransfer })
    .trigger('mouseup', { force: true, dataTransfer })
})

Cypress.Commands.add('story', (text) => cy.log(`📚 **${text}**`))
