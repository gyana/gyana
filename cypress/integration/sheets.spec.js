/// <reference types="cypress" />

const SHARED_SHEET =
  'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'
const RESTRICTED_SHEET =
  'https://docs.google.com/spreadsheets/d/16h15cF3r_7bFjSAeKcy6nnNDpi-CS-NEgUKNCRGXs1E/edit'

describe('sheets', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('connect to valid Google Sheet', () => {
    cy.contains('Add Sheet').click()

    cy.url().should('contain', '/projects/1/integrations/sheets/new')
    // pretend to share with this email account
    cy.contains('gyana-local@gyana-1511894275181.iam.gserviceaccount.com')
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('input[name=cell_range]').type('store_info!A20:D22')
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
  it('does not create for invalid URL, valid URL without access or invalid cell range', () => {
    cy.contains('Add Sheet').click()

    cy.get('input[name=url]').type('https://www.google.com')
    cy.get('button[type=submit]').click()
    cy.contains('The URL to the sheet seems to be invalid.')

    // sheet is not shared with account
    cy.get('input[name=url]').clear().type(RESTRICTED_SHEET)
    cy.get('button[type=submit]').click()
    cy.contains(
      "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
    )

    cy.get('input[name=url]').clear().type(SHARED_SHEET)
    cy.get('input[name=cell_range]').type('does_not_exist!A1:D11')
    cy.get('button[type=submit]').click()
    cy.contains('Unable to parse range: does_not_exist!A1:D11')
  })
  it('displays errors on failed sync and does not create entities or send email', () => {
    cy.contains('Add Sheet').click()

    cy.url().should('contain', '/projects/1/integrations/sheets/new')
    // pretend to share with this email account
    cy.contains('gyana-local@gyana-1511894275181.iam.gserviceaccount.com')
    cy.get('input[name=url]').type(SHARED_SHEET)
    // empty cells trigger column does not exist error
    cy.get('input[name=cell_range]').type('store_info!A20:D21')
    cy.get('button[type=submit]').click()

    cy.contains('Waiting for sync to start')
    cy.contains('Uh-Oh, something went wrong!')

    // verify that nothing was created
    cy.visit('/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', 1)
  })
})
