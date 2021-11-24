/// <reference types="cypress" />

import { getModelStartId, BIGQUERY_TIMEOUT } from '../support/utils'

const createWidget = (kind) => {
  cy.contains('Add widget').click()
  cy.contains(kind).click()
  cy.contains('This widget needs to be configured')
  cy.contains('configured').click()
  cy.contains('-----------').click()
  cy.contains('store_info').click({ force: true })
}

const widgetStartId = getModelStartId('widgets.widget')
const dashboardStartId = getModelStartId('dashboards.dashboard')
describe('dashboards', () => {
  beforeEach(() => {
    cy.login()
    cy.visit('/projects/1/dashboards/')
    cy.contains('Display data metrics and share')
  })

  it('create dashboard with two widgets', () => {
    cy.contains('Create a new dashboard').click()
    createWidget('Table')
    cy.contains('Save & Preview').should('not.be.disabled').click()
    cy.contains('Edinburgh')
    cy.get('button[class*=tf-modal__close]').click({ force: true })
    cy.get('input[value="Save & Preview"]').should('not.exist')
    cy.get(`#widget-${widgetStartId}`).contains('London')

    createWidget('Bar')
    cy.get('select[name=dimension]').select('Owner')
    cy.get('[data-formset-prefix-value=aggregations]').within((el) => {
      cy.wrap(el).get('button').click()
    })
    cy.get('select[name=aggregations-0-column]').select('Employees')
    cy.get('select[name=aggregations-0-function]').select('SUM')
    cy.contains('Save & Close').click()
    cy.get(`#widget-${widgetStartId + 1}`).within((el) => {
      cy.wrap(el).contains('text', 'David').should('be.visible')
    })

    // TODO: trigger the hover and remove the force click
    // cy.get('#widgets-output-1').trigger('mouseover')
    cy.get(`#widget-delete-${widgetStartId}`).click({ force: true })
    cy.contains('Yes').click({ force: true })
    cy.get(`#widget-${widgetStartId}`).should('not.exist')
  })

  it('created workflow shows in dashboard', () => {
    const id = getModelStartId('nodes.node')

    cy.visit('/projects/1/workflows/')
    cy.contains('Create a new workflow').click()
    cy.drag('#dnd-node-input')
    cy.drop('.react-flow')
    cy.get(`[data-id=${id}]`).dblclick()
    cy.contains('store_info').click()
    cy.contains('Save & Close').should('not.be.disabled').click()
    cy.reactFlowDrag(id, { x: 150, y: 300 })

    cy.drag('#dnd-node-output')
    cy.drop('[class=react-flow]')
    cy.get(`[data-id=${id + 1}]`).should('exist')
    cy.connectNodes(id, id + 1)
    cy.contains('Run').click()
    cy.contains('Last run')

    cy.visit('/projects/1/dashboards')
    cy.contains('Create a new dashboard').click()
    createWidget('Table')
    cy.get('select-source').find('button').click()
    cy.get('select-source').contains('Untitled - Untitled').click()

    cy.contains('Save & Preview').click()
    cy.contains('Loading widget...')
    cy.get(`#widgets-output-${widgetStartId} table`).contains('Edinburgh').should('be.visible')
  })
})
