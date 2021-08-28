/// <reference types="cypress" />

const parseUrlFromMsg = (msg) =>
  msg['payload'].split('\n').slice(-1)[0].replace("If you'd like to join, please go to ", '')

const inviteByEmail = (email) => {
  cy.contains('Invites').click()
  cy.url().should('contain', '/teams/1/invites')

  cy.contains('New Invite').click()
  cy.url().should('contain', '/teams/1/invites/new')

  cy.get('input[type=email]').type(email)
  cy.get('button[type=submit]').click()
}

describe('invites', () => {
  beforeEach(() => {
    cy.login()
    cy.visit('//teams/1')
  })
  it('invite new user to team', () => {
    inviteByEmail('invite@gyana.com')

    cy.logout()

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)

    cy.outbox().then((outbox) => {
      const url = parseUrlFromMsg(outbox['messages'][0])
      cy.visit(url)
    })

    cy.get('input[type=password]').type('seewhatmatters')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/1')
    cy.contains('Vayu')
  })
  it('invite existing user to team', () => {
    inviteByEmail('alone@gyana.com')

    cy.logout()

    cy.login('alone@gyana.com', 'seewhatmatters')

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)

    cy.outbox().then((outbox) => {
      const url = parseUrlFromMsg(outbox['messages'][0])
      cy.visit(url)
    })

    cy.url().should('contain', '/teams/1')
  })
  it('resend and delete invite', () => {
    inviteByEmail('invite@gyana.com')

    cy.get('.fa-redo-alt').click()

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 2)

    cy.get('.fa-trash').click()
    cy.contains('Yes').click()

    cy.logout()

    cy.outbox().then((outbox) => {
      const url = parseUrlFromMsg(outbox['messages'][1])
      cy.request({ url, failOnStatusCode: false })
        .then((response) => response.status)
        .should('eq', 410)
    })
  })
  it('cannot invite existing user or existing invited user', () => {
    inviteByEmail('member@gyana.com')

    cy.contains('A user with this email is already part of your team.')

    // Delete the member but invite model still exists
    cy.contains('Members').click()
    cy.contains('member@gyana.com').click()
    cy.contains('Delete').click()
    cy.contains('Yes').click()

    inviteByEmail('member@gyana.com')
    inviteByEmail('member@gyana.com')
    cy.contains('A user with this email is already invited to your team.')
  })
})
