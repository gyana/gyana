/// <reference types="cypress" />

describe('integrations', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('upload valid CSV', () => {
    cy.contains('Upload CSV').click()

    cy.url().should('contain', '/projects/1/integrations/uploads')
    cy.get('input[type=file]').attachFile('store_info.csv')
    cy.get('button[type=submit]').click()

    // bigquery file upload needs longer wait
    cy.contains('Structure', { timeout: 10000 })
    cy.contains('Data')
    cy.contains('15')

    cy.url().should('contain', '/projects/1/integrations/2')
  })
})
