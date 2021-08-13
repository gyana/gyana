/// <reference types="cypress" />

const SHARED_SHEET =
  'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'

describe('integrations', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('view structure and preview', () => {
    cy.contains('store_info').click()

    cy.url().should('contain', '/projects/1/integrations/1')

    cy.contains('Data').click()

    // structure
    cy.url().should('contain', '/projects/1/integrations/1/data')
    cy.get('table tbody tr').should('have.length', 4)
    cy.get('table tbody :first-child').should('contain', 'store_id').and('contain', 'Number')

    // preview
    cy.contains('Preview').click()
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
    cy.get('table tbody tr').should('have.length', 5)
  })
  it('create, retry, edit and approve', () => {
    // using google sheets example

    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()

    // start with runtime error
    cy.url().should('contain', '/projects/1/integrations/sheets/new')
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()

    cy.contains('Advanced').click()
    cy.get('input[name=cell_range]').type('store_info!A20:D21')
    cy.get('button[type=submit]').click()
    cy.contains('No columns found in the schema.', { timeout: 10000 })

    // check the pending page and navigate back
    cy.visit('/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', 6)

    cy.contains('Pending (1)').click()
    cy.url().should('contain', '/projects/1/integrations/pending')
    cy.get('table tbody tr').should('have.length', 1)
    cy.contains('Store info sheet').click()

    // try to retry it
    cy.contains('Retry').click()

    // it fails again
    cy.contains('No columns found in the schema.', { timeout: 10000 })

    // edit the configuration
    cy.contains('Configure').click()
    cy.contains('Advanced').click()
    cy.get('input[name=cell_range]').clear().type('store_info!A1:D11')
    cy.get('button[type=submit]').click()

    cy.contains('Confirm', { timeout: 10000 })

    // make absolute sure that only after approval does row count update
    cy.reload()
    cy.contains('Rows 25/∞')
    cy.contains('Confirm').click()
    cy.contains('Rows 35/∞')

    // check the pending page again
    cy.visit('/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', 7)

    cy.contains('Pending').click()
    cy.get('table tbody tr').should('have.length', 0)

    // todo: verify row count updates now
  })
})
