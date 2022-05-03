import fixtures from '../fixtures/fixtures.json'

export const getIframeBody = (id) => {
  // get the iframe > document > body
  // and retry until the body element is not empty
  return (
    cy
      .get(`iframe[id=${id}]`)
      .its('0.contentDocument.body')
      .should('not.be.empty')
      // wraps "body" DOM element to allow
      // chaining more Cypress commands, like ".find(...)"
      // https://on.cypress.io/wrap
      .then(cy.wrap)
  )
}

export const getModelStartId = (modelname) =>
  Math.max(
    ...fixtures
      .filter((fixture) => fixture.model == modelname)
      .map((fixture) => fixture.pk),
    0
  ) + 1

// pending and ready integrations for the main test project

const projectId = 1

export const readyIntegrations = fixtures.filter(
  (fixture) =>
    fixture.model == 'integrations.integration' &&
    fixture.fields.ready &&
    fixture.fields.project == projectId
).length

export const pendingIntegrations = fixtures.filter(
  (fixture) =>
    fixture.model == 'integrations.integration' &&
    !fixture.fields.ready &&
    fixture.fields.project == projectId
).length

export const BIGQUERY_TIMEOUT = 10000
