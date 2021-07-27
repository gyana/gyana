/// <reference types="cypress" />

describe('teams', () => {
  beforeEach(() => {
    cy.login()
  })
  it('create, read, update and delete', () => {
    cy.visit('/')

    cy.contains('Vayu')

    cy.get('#sidebar-newteam').click()
    cy.url().should('contain', '/teams/new')

    cy.get('input[type=text]').type('Neera')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/2')
    cy.contains('Neera')
  })
})
