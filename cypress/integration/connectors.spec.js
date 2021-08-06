/// <reference types="cypress" />

describe('integrations', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('connect to Fivetran', () => {
    cy.contains('New Integration').click()

    cy.url().should('contain', '/projects/1/integrations/new')
    // all Fivetran connectors are mocked via MockFivetranClient
    cy.contains('Google Analytics').click()

    cy.url().should('contain', '/projects/1/integrations/create')
    cy.get('input[name=name]').type('Google Analytics')
    cy.get('button[type=submit]').click()

    // the uuid is non-deterministic
    cy.url().should('contain', '/projects/1/integrations/').and('contain', '/setup')
    cy.get('button[type=submit]').click()

    // TODO: test data is available
  })
})
