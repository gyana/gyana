/// <reference types="cypress" />

describe('uploads', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('upload valid CSV', () => {
    cy.contains('New Integration').click()
    cy.contains('Upload CSV').click()

    cy.url().should('contain', '/projects/1/integrations/uploads/new')
    cy.get('input[type=file]').attachFile('store_info.csv')
    cy.contains('File uploaded')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/projects/1/integrations/uploads/2')
    cy.contains('Validating and importing your file...')
    cy.contains('File successfully validated and imported.')

    // // bigquery file upload needs longer wait
    cy.contains('Structure', { timeout: 10000 })
    cy.contains('Data')
    cy.contains('15')

    cy.url().should('contain', '/projects/1/integrations/3')
  })
})
