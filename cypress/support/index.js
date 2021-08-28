// ***********************************************************
// This example support/index.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'
import './turbo'
import './vcr'

beforeEach(function () {
  // reset and seed the database prior to every test
  cy.request({
    method: 'GET',
    url: '/cypress/resetdb',
  })
  // start recording external requests for fast playback
  cy.startVCR(this.currentTest.parent.title, this.currentTest.title)
})

afterEach(function () {
  if (this.currentTest.state == 'passed') {
    cy.stopVCR()
  }
})
