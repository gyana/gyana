/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const createWidget = (kind, offsetX, offsetY) => {
  cy.drag(`#widget-${kind}`)
  cy.drop('.widgets', { offsetX, offsetY })
  cy.get('[data-cy=widget-configure]').click()
  cy.get('gy-select-source[name=table]').click()
  cy.contains('store_info').click({ force: true })
}

const widgetStartId = getModelStartId('widgets.widget')
const dashboardStartId = getModelStartId('dashboards.dashboard')

describe('dashboards', () => {
  beforeEach(() => {
    cy.login()
    cy.visit('/projects/1/dashboards/')
  })

  it('dashboard editor', () => {
    cy.get('[data-cy=dashboard-create]').click()
    cy.get('input[id=name]').clear().type('Magical dashboard{enter}')

    // create a table widget and view in the dashboard
    createWidget('table', 0, 0)
    cy.contains('Save & Preview').should('not.be.disabled').click()
    cy.contains('Edinburgh')

    cy.get('button[class*=tf-modal__close]').click({ force: true, turbo: false })
    cy.get('input[value="Save & Preview"]').should('not.exist')
    cy.get(`#widget-${widgetStartId}`).contains('London')

    // chart with aggregrations
    createWidget('msbar2d', 0, 400)
    cy.get('select[name=dimension]').select('Owner')
    cy.get('[data-formset-prefix-value=aggregations]').within((el) => {
      cy.wrap(el).get('button').should('not.be.disabled').click({ turbo: false })
    })
    cy.get('select[name=aggregations-0-column]').select('Employees')
    cy.get('select[name=aggregations-0-function]').select('SUM')
    cy.contains('Save & Close').click()
    cy.get(`#widget-${widgetStartId + 1}`).within((el) => {
      // TODO: check for visibility
      cy.wrap(el).contains('text', 'David')
    })

    // delete a widget
    cy.get(`#widget-delete-${widgetStartId}`).click({ force: true })
    cy.get(`#widget-${widgetStartId}`).should('not.exist')

    // share
    cy.get(`#dashboard-share-${dashboardStartId}`).click()
    cy.get('select[name=shared_status]').select('public')
    cy.get('#dashboard-share-update').click()

    cy.contains(
      /localhost:8000\/dashboards\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/
    )
      .invoke('text')
      .then((text) => {
        const sharedUrl = text.trim()
        cy.logout()

        cy.visit(sharedUrl)
        cy.contains('David')
      })
  })
})
