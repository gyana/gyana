/// <reference types="cypress" />

describe('sign up', () => {
  it('signs in headlessly', () => {
    cy.login()

    cy.visit('/')
  })

  it('signs up to app', () => {
    cy.visit('/accounts/signup')

    cy.get('input[type=email]').type('new@gyana.com')
    cy.get('input[type=password]').type('seewhatmatters')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/teams/new')

    cy.get('input[type=text]').type('New')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/teams/2')
  })

  it('does this', () => {
    cy.visit('/')

    cy.contains('Forgot password?').click()
    cy.url().should('contain', '/accounts/password/reset')
    cy.contains('Password Reset')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/accounts/password/reset/done')
    cy.contains('Password Reset')

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][0]
      const url = msg['payload'].split('\n').filter((x) => x.startsWith('http'))[0]
      cy.visit(url)
    })
    cy.url().should('contain', 'accounts/password/reset/key/1-set-password')
    cy.contains('Change Password')

    cy.get('input[type=password]').first().type('senseknowdecide')
    cy.get('input[type=password]').last().type('senseknowdecide')
    cy.get('input[type=submit]').click()
    cy.url().should('contain', 'accounts/password/reset/key/done')
    cy.contains('Your password has been changed.')

    cy.visit('/')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('input[type=password]').type('senseknowdecide')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/1')
  })
})
