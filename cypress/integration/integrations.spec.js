/// <reference types="cypress" />

describe('integrations', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('upload valid CSV', () => {
    cy.contains('Upload CSV').click()

    cy.url().should('contain', '/projects/1/integrations/upload')
    cy.get('input[type=file]').attachFile('store_info.csv')
    cy.get('button[type=submit]').click()

    // bigquery file upload needs longer wait
    cy.contains('Structure', { timeout: 10000 })
    cy.contains('Data')
    cy.contains('15')

    cy.url().should('contain', '/projects/1/integrations/2')
  })
  it.only('connect to Google Sheet', () => {
    cy.contains('New Integration').click()

    cy.url().should('contain', '/projects/1/integrations/new')
    cy.contains('Google Sheets').click()

    cy.get('input[name=url]').type(
      'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'
    )
    cy.get('input[name=name]').type('Stores info')
    cy.get('input[name=cell_range]').type('A1:D11')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/projects/1/integrations/2')
    cy.contains("Syncing, you'll get an email when it is ready")
    cy.contains('tasks processed')
    cy.get('Reload to see results').click()

    cy.contains('Structure')
    cy.contains('Data')
    cy.contains('10')
  })
})
