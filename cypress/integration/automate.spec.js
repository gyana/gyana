import { BIGQUERY_TIMEOUT } from '../support/utils'

describe('automate', () => {
  it('automate editor', () => {
    cy.login()
    cy.visit('/projects/1/automate')

    cy.get('button[data-cy=project-run]').click()

    cy.get('[data-cy-status=running]').should('have.length', 1)
    cy.get('[data-cy-status=pending]').should('have.length', 2)

    const initial = 2

    cy.get('[data-cy-status=success]', { timeout: BIGQUERY_TIMEOUT }).should(
      'have.length',
      initial + 1
    )
    cy.get('[data-cy-status=success]', { timeout: BIGQUERY_TIMEOUT }).should(
      'have.length',
      initial + 2
    )
    cy.get('[data-cy-status=success]', { timeout: BIGQUERY_TIMEOUT }).should(
      'have.length',
      initial + 3
    )

    cy.get('button[data-cy=settings]').click()
    cy.get('table tbody tr').should('have.length', 1)
  })
})
