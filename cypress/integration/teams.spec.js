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
})
