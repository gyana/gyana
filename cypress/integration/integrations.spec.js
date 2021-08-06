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
  it('connect to Google Sheet', () => {
    cy.contains('New Integration').click()

    cy.url().should('contain', '/projects/1/integrations/new')
    cy.contains('Google Sheets').click()

    // pretend to share with this email account
    cy.contains('gyana-local@gyana-1511894275181.iam.gserviceaccount.com')
    cy.get('input[name=url]').type(
      'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'
    )
    cy.get('input[name=name]').type('Stores info')
    cy.get('input[name=cell_range]').type('store_info!A1:D11')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/projects/1/integrations/2')
    cy.contains("Syncing, you'll get an email when it is ready")
    cy.contains('tasks processed')
    cy.contains('Reload to see results').click()

    cy.contains('Structure')
    cy.contains('Data')
    cy.contains('10')
  })
  it.only('connect to Fivetran', () => {
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
