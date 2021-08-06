/// <reference types="cypress" />

describe('integrations', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('view structure and data', () => {
    cy.contains('store_info').click()

    cy.url().should('contain', '/projects/1/integrations/1')

    cy.contains('Structure').click()
    cy.url().should('contain', '/projects/1/integrations/1/structure')
    cy.get('table tbody tr').should('have.length', 4)
    cy.get('table tbody :first-child').should('contain', 'store_id').and('contain', 'int64')

    cy.contains('Data').click()
    cy.url().should('contain', '/projects/1/integrations/1/data')
    cy.get('table tbody tr').should('have.length', 15)
    cy.get('table thead th').should('have.length', 4)
  })
  it('update and delete', () => {
    cy.contains('store_info').click()

    // update

    cy.get('#tabbar').within(() => cy.contains('Settings').click())

    cy.url().should('contain', '/projects/1/integrations/1/settings')
    cy.get('#main').within(() => cy.get('input[name=name]').clear().type('Store Info'))
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/projects/1/integrations/1')
    // the integration title is an editable input
    cy.get('input[value="Store Info"]')

    // delete

    cy.get('#tabbar').within(() => cy.contains('Settings').click())

    cy.contains('Delete').click()
    cy.contains('Yes').click()

    cy.url().should('contain', '/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', 0)
  })
})
