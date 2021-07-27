/// <reference types="cypress" />

describe('teams', () => {
  beforeEach(() => {
    cy.login()
  })
  it('create, read, update and delete', () => {
    cy.visit('/')

    cy.get('#heading').within(() => cy.contains('Vayu'))

    // create
    cy.get('#sidebar-newteam').click()
    cy.url().should('contain', '/teams/new')

    cy.get('input[type=text]').type('Neera')
    cy.get('button[type=submit]').click()

    // view
    cy.url().should('contain', '/teams/2')
    cy.get('#heading').within(() => cy.contains('Neera'))

    // switch
    cy.get('#sidebar').within(() => {
      cy.contains('Vayu').click()
    })
    cy.get('#heading').within(() => cy.contains('Vayu'))
    cy.get('#sidebar').within(() => {
      cy.contains('Neera').click()
    })
    cy.get('#heading').within(() => cy.contains('Neera'))

    // update
    cy.contains('Settings').click()
    cy.url().should('contain', '/teams/2/update')
    cy.get('input[type=text]').clear().type('Agni')
    cy.get('button[type=submit]').click()
    cy.get('#heading').within(() => cy.contains('Agni'))

    // delete
    cy.contains('Delete').click()
    cy.url().should('contain', '/teams/2/delete')
    cy.get('button[type=submit]').click()
    cy.get('#sidebar').contains('Agni').should('not.exist')
  })
  it('invite new user to team', () => {
    cy.visit('/')

    cy.contains('Invites').click()
    cy.url().should('contain', '/teams/1/invites')

    cy.contains('New Invite').click()
    cy.url().should('contain', '/teams/1/invites/new')

    cy.get('input[type=email]').type('invite@gyana.com')
    cy.get('button[type=submit]').click()

    cy.logout()

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][0]
      const url = msg['payload']
        .split('\n')
        .slice(-1)[0]
        .replace("If you'd like to join, please go to ", '')
      cy.visit(url)
    })

    cy.get('input[type=password]').type('seewhatmatters')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/1')
    cy.contains('Vayu')
  })
  it('invite existing user to team', () => {
    cy.visit('/')

    cy.contains('Invites').click()
    cy.url().should('contain', '/teams/1/invites')

    cy.contains('New Invite').click()
    cy.url().should('contain', '/teams/1/invites/new')

    cy.get('input[type=email]').type('alone@gyana.com')
    cy.get('button[type=submit]').click()

    cy.logout()

    cy.login('alone@gyana.com', 'seewhatmatters')

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][0]
      const url = msg['payload']
        .split('\n')
        .slice(-1)[0]
        .replace("If you'd like to join, please go to ", '')
      cy.visit(url)
    })

    cy.url().should('contain', '/teams/1')
  })
  it('resend and delete invite', () => {
    cy.visit('/')

    cy.contains('Invites').click()
    cy.url().should('contain', '/teams/1/invites')

    cy.contains('New Invite').click()
    cy.url().should('contain', '/teams/1/invites/new')

    cy.get('input[type=email]').type('invite@gyana.com')
    cy.get('button[type=submit]').click()

    cy.get('.fa-redo-alt').click()

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 2)

    cy.get('.fa-trash').click()
    cy.contains('Yes').click()

    cy.logout()

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][1]
      const url = msg['payload']
        .split('\n')
        .slice(-1)[0]
        .replace("If you'd like to join, please go to ", '')
      cy.request({ url, failOnStatusCode: false })
        .then((response) => response.status)
        .should('eq', 410)
    })
  })
})
