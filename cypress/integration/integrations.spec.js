/// <reference types="cypress" />

import { readyIntegrations, pendingIntegrations, BIGQUERY_TIMEOUT } from '../support/utils'

const SHARED_SHEET =
  'https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit'

describe('integrations', () => {
  it('create a sheet integration with retry', () => {
    cy.visit('/projects/1')

    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()

    // start with runtime error
    cy.url().should('contain', '/projects/1/integrations/sheets/new')
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()

    cy.get('input[name=cell_range]').type('store_info!A20:D21')
    cy.get('button[type=submit]').click()
    cy.contains('No columns found in the schema.', { timeout: BIGQUERY_TIMEOUT })

    // check the pending page and navigate back
    cy.visit('/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', readyIntegrations)

    cy.contains(`Pending (${1 + pendingIntegrations})`).click()
    cy.url().should('contain', '/projects/1/integrations/pending')
    cy.get('table tbody tr').should('have.length', 1 + pendingIntegrations)
    cy.contains('Store info sheet').click()

    // try to retry it
    cy.contains('Retry').click()

    // it fails again
    cy.contains('No columns found in the schema.', { timeout: BIGQUERY_TIMEOUT })

    // edit the configuration
    cy.get('#main').within(() => cy.contains('Configure').click())
    cy.get('input[name=cell_range]').clear().type('store_info!A1:D11')
    cy.get('button[type=submit]').click()

    cy.contains('Confirm', { timeout: BIGQUERY_TIMEOUT }).click()

    // check the pending page again
    cy.visit('/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', readyIntegrations + 1)

    cy.contains('Pending').click()
    cy.get('table tbody tr').should('have.length', pendingIntegrations)
  })
})
