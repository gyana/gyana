/// <reference types="cypress" />

describe('users', () => {
  it('signs in to app', () => {
    cy.visit('/')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('input[type=password]').type('seewhatmatters')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/1')
  })

  it('signs up to app', () => {
    cy.visit('/')

    cy.contains('create one here').click()
    cy.url().should('contain', '/accounts/signup')

    cy.get('input[type=email]').type('new@gyana.com')
    cy.get('input[type=password]').type('seewhatmatters')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/teams/new')

    cy.get('input[type=text]').type('New')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/teams/3')
  })

  it('resets password', () => {
    cy.visit('/')

    cy.contains('Forgot password?').click()
    cy.url().should('contain', '/accounts/password/reset')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/accounts/password/reset/done')

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][0]
      const url = msg['payload'].split('\n').filter((x) => x.startsWith('http'))[0]
      cy.visit(url)
    })
    cy.url().should('contain', 'accounts/password/reset/key/1-set-password')

    cy.get('input[type=password]').first().type('senseknowdecide')
    cy.get('input[type=password]').last().type('senseknowdecide')
    cy.get('input[type=submit]').click()
    cy.url().should('contain', 'accounts/password/reset/key/done')

    cy.visit('/')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('input[type=password]').type('senseknowdecide')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/1')
  })

  it('signs out', () => {
    cy.login()

    cy.visit('/')

    cy.get('#sidebar-profile').click()
    cy.url().should('contain', '/users/profile')

    cy.contains('Sign out').click()

    cy.url().should('contain', '/accounts/login')

    cy.visit('/users/profile')

    cy.url().should('contain', '/accounts/login')
  })
})
