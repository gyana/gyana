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

const outbox = () => cy.request('/cypress/outbox').then((response) => response.body)

Cypress.Commands.add('outbox', outbox)

// Adapted from https://github.com/cypress-io/cypress/issues/1938#issuecomment-502201139
Cypress.Commands.overwrite('click', (originalFn, subject, ...args) => {
  var lastArg = args.length ? args[args.length - 1] : {}
  // Check if turbo could be active for this click event - could be improved
  if (
    (typeof lastArg !== 'object' || !lastArg['noWaiting']) &&
    ((subject[0].tagName === 'A' && subject[0].getAttribute('href')) ||
      subject[0].getAttribute('type') === 'submit')
  ) {
    // Wait for turbo to finish loading the page before proceeding with the next Cypress instructions.
    // First, get the document
    cy.document({ log: false }).then(($document) => {
      Cypress.log({
        $el: subject,
        name: 'click',
        displayName: 'click',
        message: 'click and wait for page to load',
        consoleProps: () => ({ subject: subject }),
      })
      // Make Cypress wait for this promise which waits for the turbo:load event
      return new Cypress.Promise((resolve) => {
        // Once we receive the event,
        const onTurbolinksLoad = () => {
          // clean up
          $document.removeEventListener('turbo:load', onTurbolinksLoad)
          // signal to Cypress that we're done
          resolve()
        }
        // Add our logic as event listener
        $document.addEventListener('turbo:load', onTurbolinksLoad)
        // Finally, we are ready to perform the actual click operation
        originalFn(subject, ...args)
      })
    })
  } else {
    // Not a normal click on an <a href> tag, turbo will not interfere here
    return originalFn(subject, ...args)
  }
})
