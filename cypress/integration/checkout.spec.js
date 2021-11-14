/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const newTeamId = getModelStartId('teams.team')

const getIframeDocument = () => {
  return (
    cy
      .get('iframe[id=pf_18567]')
      // Cypress yields jQuery element, which has the real
      // DOM element under property "0".
      // From the real DOM iframe element we can get
      // the "document" element, it is stored in "contentDocument" property
      // Cypress "its" command can access deep properties using dot notation
      // https://on.cypress.io/its
      .its('0.contentDocument')
      .should('exist')
  )
}

const getIframeBody = () => {
  // get the document
  return (
    getIframeDocument()
      // automatically retries until body is loaded
      .its('body')
      .should('not.be.undefined')
      // wraps "body" DOM element to allow
      // chaining more Cypress commands, like ".find(...)"
      .then(cy.wrap)
  )
}

describe('checkout', () => {
  it('pay for pro', () => {
    cy.login()
    cy.visit('/')

    // new team with no billing
    cy.get('#sidebar-newteam').click()
    cy.get('input[name=name]').type('No billing')
    cy.get('button[type=submit]').click({ turbo: false })

    // billing
    cy.get('#sidebar').within(() => cy.contains('Billing').click())
    cy.url().should('contain', `/teams/${newTeamId}/account`)

    // view plans with dynamic pricing
    cy.contains('Upgrade').click({ turbo: false })
    cy.url().should('contain', `/teams/${newTeamId}/plans`)
    cy.get('.paddle-gross').first().should('not.be.empty')

    // checkout with dynamic pricing
    cy.contains('Upgrade to Pro').click({ turbo: false })
    cy.url().should('contain', `/teams/${newTeamId}/checkout`)
    cy.get('span[data-paddle-target=total]').should('not.be.empty')
    cy.get('span[data-paddle-target=recurring]').should('not.be.empty')

    // complete payment
    getIframeBody().find('input[name=postcode]').type('MK3 6EB')
    getIframeBody().find('button[type=submit]').click({ turbo: false })

    getIframeBody()
      .find('button[data-testid=SPREEDLY_CARD_PaymentSelectionButton]')
      .first()
      .click({ turbo: false })

    getIframeBody().find('input[name=cardNumber]').type('4242424242424242')
    getIframeBody().find('input[name=name]').type('Gyana')
    getIframeBody().find('input[name=month]').type('12')
    getIframeBody().find('input[name=year]').type('2024')
    getIframeBody().find('input[name=cvv]').type('111')
    getIframeBody().find('button[data-testid=cardPaymentFormSubmitButton]').click({ turbo: false })

    getIframeBody().find('[data-testid=paymentSuccess]', { timeout: 10000 })

    // validate
    cy.contains('Go to billing').click()
    cy.contains('Information about your new subscription will be available here in a moment.')
  })
})
