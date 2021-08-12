/// <reference types="cypress" />

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

    cy.url().should('contain', '/projects/1/integrations/7/setup')
    cy.contains('Save & Run').click()

    cy.contains('Importing data from your connector...')
    cy.contains('Connector successfully imported.', { timeout: 10000 })

    cy.contains('Approve').click()

    // connector created successfully
    cy.contains('Structure')
    cy.contains('Data')

    // check email sent
    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)
  })
  it('checks status on pending page', () => {
    // start the connector
    cy.visit('/projects/1/integrations/connectors/new?service=google_analytics')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/connectors/mock')
    cy.contains('continue').click()
    cy.url().should('contain', '/projects/1/integrations/7/setup')
    cy.contains('Save & Run').click()

    // wait 1s for mock connector to complete
    cy.wait(1000)

    // check the pending page
    cy.visit('/projects/1/integrations/pending')
    cy.get('table tbody tr').should('have.length', 1)

    // initially it is loading
    cy.get('.fa-circle-notch').should('have.length', 1)
    cy.get('.fa-check-circle').should('not.exist')

    // now it is completed
    cy.get('.fa-circle-notch').should('not.exist')
    cy.get('.fa-check-circle').should('have.length', 1)

    // takes me to the review page
    cy.contains('Google Analytics').first().click()

    cy.url().should('contain', '/projects/1/integrations/7/setup')
    cy.contains('Approve').click()

    cy.url().should('contain', '/projects/1/integrations/7')
  })
})
