/// <reference types="cypress" />

import { getModelStartId, pendingIntegrations, BIGQUERY_TIMEOUT } from '../support/utils'

const createConnector = (service) => {
  cy.visit('/projects/1/integrations/connectors/new?service=google_analytics')
  cy.get('button[type=submit]').click()
  cy.url().should('contain', '/connectors/mock')
  cy.contains('continue').click()
}

const newConnectorId = getModelStartId('integrations.integration')

describe('connectors', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('connect to Fivetran', () => {
    cy.contains('New Integration').click()
    cy.contains('New Connector').click()

    cy.url().should('contain', '/projects/1/integrations/connectors/new')
    // all Fivetran connectors are mocked via MockFivetranClient
    cy.contains('Google Analytics').click()

    cy.url().should('contain', '/projects/1/integrations/connectors/new?service=google_analytics')
    cy.get('button[type=submit]').click()

    // mock fivetran redirect
    cy.url().should('contain', '/connectors/mock')
    cy.contains('continue').click()

    cy.url().should('contain', `/projects/1/integrations/${newConnectorId}/configure`)
    cy.get('button[type=submit]').click()

    cy.contains('Validating and importing your connector...')
    cy.contains('Connector successfully validated and imported.', { timeout: BIGQUERY_TIMEOUT })

    cy.contains('Confirm').click()

    // connector created successfully
    cy.contains('Data')

    // check email sent
    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)
  })
  it('checks status on pending page', () => {
    createConnector('google_analytics')
    cy.get('button[type=submit]').click()

    // wait 1s for mock connector to complete
    cy.wait(1000)

    // check the pending page
    cy.visit('/projects/1/integrations/pending')
    cy.get('table tbody tr').should('have.length', 1 + pendingIntegrations)

    // initially it is loading
    cy.get('.fa-circle-notch').should('have.length', 1)
    cy.get('.fa-exclamation-triangle').should('have.length', 4)

    // now it is completed
    cy.get('.fa-circle-notch').should('not.exist')
    cy.get('.fa-exclamation-triangle').should('have.length', 5)

    // takes me to the review page
    cy.contains('Google Analytics').first().click()

    cy.url().should('contain', `/projects/1/integrations/${newConnectorId}/done`)
    cy.contains('Confirm').click()

    cy.url().should('contain', `/projects/1/integrations/${newConnectorId}`)
  })
  it('update tables in non-database', () => {
    createConnector('google_analytics')

    // remove a table
    cy.contains('Advanced').click()
    cy.contains('Adwords Campaigns').click()
    // wait for javascript to update hidden element
    cy.wait(200)
    cy.get('button[type=submit]').click()

    // reloading speeds up mock sync
    cy.wait(1000)
    cy.reload()

    cy.contains('Review your imported data', { timeout: BIGQUERY_TIMEOUT })
    cy.contains('Adwords Campaigns').should('not.exist')
  })
})
