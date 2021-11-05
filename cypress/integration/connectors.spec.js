/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const newConnectorId = getModelStartId('integrations.integration')

describe('connectors', () => {
  it('connect to google analytics with mock fivetran client', () => {
    cy.login()
    cy.visit('/projects/1/integrations')

    cy.contains('New Integration').click()
    cy.contains('New Connector').click({ force: true })

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

    cy.contains('Validating and importing your Google Analytics connector...')
    // need to explicitly reload as we're not using celery progress
    cy.wait(1000)
    cy.reload()

    cy.contains('Confirm').click()

    // connector created successfully
    cy.get('#tabbar').within(() => cy.contains('Overview'))
  })
})
