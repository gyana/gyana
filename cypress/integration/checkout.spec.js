/// <reference types="cypress" />

import { getIframeBody, getModelStartId } from '../support/utils'

const newTeamId = getModelStartId('teams.team')

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

    // view plans
    cy.contains('Upgrade').click({ turbo: false })
    cy.url().should('contain', `/teams/${newTeamId}/pricing`)

    // checkout
    getIframeBody('pricing').contains('Upgrade to Pro').click({ turbo: false })
    cy.url().should('contain', `/teams/${newTeamId}/checkout`)
    cy.get('span[data-paddle-target=total]').should('not.be.empty')
    cy.get('span[data-paddle-target=recurring]').should('not.be.empty')

    // complete payment
    getIframeBody('pf_18567').find('input[name=postcode]').type('MK3 6EB')
    getIframeBody('pf_18567')
      .find('button[type=submit]')
      .click({ turbo: false })

    getIframeBody('pf_18567')
      .find('button[data-testid=SPREEDLY_CARD_PaymentSelectionButton]')
      .first()
      .click({ turbo: false })

    getIframeBody('pf_18567')
      .find('input[name=cardNumber]')
      .type('4242424242424242')
    getIframeBody('pf_18567').find('input[name=name]').type('Gyana')
    getIframeBody('pf_18567').find('input[name=month]').type('12')
    getIframeBody('pf_18567').find('input[name=year]').type('2024')
    getIframeBody('pf_18567').find('input[name=cvv]').type('111')
    getIframeBody('pf_18567')
      .find('button[data-testid=cardPaymentFormSubmitButton]')
      .click({ turbo: false })

    getIframeBody('pf_18567').find('[data-testid=paymentSuccess]', {
      timeout: 20000,
    })

    // validate
    cy.contains('Go to billing').click()
    cy.contains(
      'Information about your new subscription will be available here in a moment.'
    )
  })
})
