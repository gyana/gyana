/// <reference types="cypress" />

describe('integrations', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('connect to Google Sheet', () => {
    cy.contains('Add Sheet').click()

    cy.url().should('contain', '/projects/1/integrations/sheets/new')
    // pretend to share with this email account
    cy.contains('gyana-local@gyana-1511894275181.iam.gserviceaccount.com')
    cy.get('input[name=url]').type(
      'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'
    )
    cy.get('input[name=cell_range]').type('store_info!A1:D11')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/projects/1/integrations/sheets/1')
    cy.contains("Syncing, you'll get an email when it is ready")
    cy.contains('Sync started')
    cy.contains('tasks processed')
    cy.contains('Reload to see results').click()

    cy.url().should('contain', '/projects/1/integrations/2')
    // Google Sheet name inferred
    cy.get('input[name=name]').should('have.value', 'Store info sheet')

    cy.contains('Structure')
    cy.contains('Data')
    cy.contains('10')
  })
})
