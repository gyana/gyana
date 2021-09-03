/// <reference types="cypress" />

import { getModelStartId, readyIntegrations, BIGQUERY_TIMEOUT } from '../support/utils'

const SHARED_SHEET =
  'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'
const RESTRICTED_SHEET =
  'https://docs.google.com/spreadsheets/d/16h15cF3r_7bFjSAeKcy6nnNDpi-CS-NEgUKNCRGXs1E/edit'

const id = getModelStartId('integrations.integration')

describe('sheets', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('connect to valid Google Sheet', () => {
    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()

    cy.url().should('contain', '/projects/1/integrations/sheets/new')
    // pretend to share with this email account
    cy.contains('gyana-local@gyana-1511894275181.iam.gserviceaccount.com')
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()

    // set advanced configuration
    cy.url().should('contain', `/projects/1/integrations/${id}/configure`)
    cy.contains('Advanced').click()
    cy.get('input[name=cell_range]').type('store_info!A1:D11')
    cy.get('button[type=submit]').click()

    cy.contains('Validating and importing your sheet...')
    cy.contains('Sheet successfully validated and imported.', { timeout: BIGQUERY_TIMEOUT })

    // review the table and approve
    cy.contains('Employees')
    cy.contains('Confirm').click()

    cy.url().should('contain', `/projects/1/integrations/${id}`)
    // Google Sheet name inferred
    cy.get('input[name=name]').should('have.value', 'Store info sheet')

    cy.contains('Data')
    cy.contains('10')

    // check email sent
    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)
  })
  it('validation failures', () => {
    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()

    // not a valid url
    cy.get('input[name=url]').type('https://www.google.com')
    cy.get('button[type=submit]').click()
    cy.contains('The URL to the sheet seems to be invalid.')

    // not shared with our service account
    cy.get('input[name=url]').clear().type(RESTRICTED_SHEET)
    cy.get('button[type=submit]').click()
    cy.contains(
      "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
    )

    // invalid cell range
    cy.get('input[name=url]').clear().type(SHARED_SHEET)
    cy.get('button[type=submit]').click()

    cy.contains('Advanced').click()
    cy.get('input[name=cell_range]').type('does_not_exist!A1:D11')
    cy.get('button[type=submit]').click()

    cy.contains('Unable to parse range: does_not_exist!A1:D11')
  })
  it('runtime failures', () => {
    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()

    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()

    // empty cells trigger column does not exist error
    cy.contains('Advanced').click()
    cy.get('input[name=cell_range]').type('store_info!A20:D21')
    cy.get('button[type=submit]').click()

    cy.contains('Validating and importing your sheet...')
    cy.contains('Errors occurred when validating your sheet')
    cy.contains('No columns found in the schema.')

    // verify that nothing was created
    cy.visit('/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', readyIntegrations)
    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 0)
    // todo: verify table is not created?
  })
  it('re-sync after source update', () => {
    cy.contains('Store info sheet').click()

    // sheet is already out of date by design
    cy.contains('This Google Sheet was updated since the last sync.')
    cy.contains('Import the latest data').click()

    cy.url().should('contain', '/projects/1/integrations/2/configure')
    cy.contains('Configure').click()
    cy.get('button[type=submit]').click()

    // the integration page has updated to link here
    cy.visit('/projects/1/integrations/2')
    cy.contains('View import in progress.').click()

    // sync is complete  and it redirects me back again
    cy.url().should('contain', '/projects/1/integrations/2/configure')
    cy.contains('Sheet successfully validated and imported.', { timeout: BIGQUERY_TIMEOUT })

    cy.visit('/projects/1/integrations/2')
    cy.contains("You've already synced the latest data.")
  })
  it('update the cell range and re-sync', () => {
    cy.contains('Store info sheet').click()

    cy.get('#tabbar').within(() => cy.contains('Setup').click())
    cy.contains('Configure').click()

    cy.contains('Advanced').click()
    cy.get('input[name=cell_range]').clear().type('store_info!A1:D6')
    cy.get('button[type=submit]').click()

    cy.contains('Sheet successfully validated and imported.', { timeout: BIGQUERY_TIMEOUT })

    // new cell range includes 5 rows of data
    cy.get('#tabbar').within(() => cy.contains('Overview').click())
    cy.contains('5')
  })
  it('all string', () => {
    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()

    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()
    cy.contains('Advanced').click()
    cy.get('input[name=cell_range').type("'store_info_all_string'")
    cy.get('button[type=submit]').click()
    // needs longer to do 3x imports
    cy.contains('Sheet successfully validated and imported.', { timeout: BIGQUERY_TIMEOUT })

    // import has inferred correct column headings
    cy.contains('Location_name')
    cy.contains('string_field_0').should('not.exist')
  })
})
