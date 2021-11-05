/// <reference types="cypress" />

import { BIGQUERY_TIMEOUT } from '../support/utils'

const SHARED_SHEET =
  'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'

describe('integrations', () => {
  it('create a sheet integration with retry', () => {
    cy.login()
    cy.visit('/projects/1')

    // todo: zero state
    cy.contains('2 integrations').click()
    cy.url().should('contain', '/projects/1/integrations')

    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click({ force: true })

    // start with runtime error
    cy.url().should('contain', '/projects/1/integrations/sheets/new')
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()

    cy.get('input[name=cell_range]').type('store_info!A20:D21')
    cy.get('button[type=submit]').click()
    cy.contains('No columns found in the schema.', { timeout: BIGQUERY_TIMEOUT })

    // try to retry it
    cy.contains('Retry').click()

    // edit the configuration
    cy.get('#main').within(() => cy.contains('Configure').click())
    cy.get('input[name=cell_range]').clear().type('store_info!A1:D11')
    cy.get('button[type=submit]').click()

    cy.contains('Confirm', { timeout: BIGQUERY_TIMEOUT }).click()
    // only 10/15 rows imported
    cy.contains('10 rows')

    // todo: next step in the flow
  })
})
