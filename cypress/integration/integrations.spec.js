/// <reference types="cypress" />

import { readyIntegrations, pendingIntegrations, BIGQUERY_TIMEOUT } from '../support/utils'

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

    cy.get('a').contains('Delete').click()
    cy.contains('Yes').click()

    cy.url().should('contain', '/projects/1/integrations')
    cy.get('table tbody tr').should('have.length', readyIntegrations - 1)
  })
  it('create, retry, edit and approve', () => {
    // using google sheets example

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
  it('row limits', () => {
    // project in team 2, with row limit of 25
    cy.visit('/projects/3/integrations')

    // add a valid sheet with 15 rows, validate row count updates on confirmation
    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()
    cy.get('button[type=submit]').click()
    cy.contains('Confirm', { timeout: BIGQUERY_TIMEOUT })

    // make absolute sure that only after approval does row count update
    cy.visit('/teams/2/account')
    cy.contains('0 / 15')
    cy.go('back')
    // confirm button is enabled
    cy.contains('Confirm').click()
    cy.visit('/teams/2/account')
    cy.contains('15 / 15')
    cy.go('back')

    // add another valid sheet, validate row count updates on confirmation
    cy.visit('/projects/3/integrations')
    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()
    cy.get('button[type=submit]').click()

    cy.contains('Insufficient rows', { timeout: BIGQUERY_TIMEOUT })
    cy.contains(
      'Adding this data will bring your total rows to 30, which exceeds your row limit of 15.'
    )
    cy.get('button[type=submit]').should('not.exist')
  })
  it('pending cleanup', () => {
    cy.get('table tbody tr').should('have.length', 2)

    // new sheet, should not get cleaned up
    cy.contains('New Integration').click()
    cy.contains('Add Sheet').click()
    cy.get('input[name=url]').type(SHARED_SHEET)
    cy.get('button[type=submit]').click()

    cy.visit('/projects/1/integrations/pending')

    cy.get('table tbody tr').should('have.length', 5)

    // trigger pending job
    cy.periodic()

    // only the pending one we just added remains
    cy.reload()
    cy.get('table tbody tr').should('have.length', 1)

    // all ready integrations are fine
    cy.visit('projects/1/integrations')
    cy.get('table tbody tr').should('have.length', 2)
  })
})
