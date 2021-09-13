/// <reference types="cypress" />

import { getModelStartId, BIGQUERY_TIMEOUT } from '../support/utils'

const createWidget = (kind) => {
  cy.contains('Add widget').click()
  cy.contains(kind).click()
  cy.contains('This widget needs to be configured!')
  cy.contains('configured').click()
  cy.contains('-----------').click()
  cy.contains('store_info').click()
}

const widgetStartId = getModelStartId('widgets.widget')
const dashboardStartId = getModelStartId('dashboards.dashboard')
describe('dashboards', () => {
  beforeEach(() => {
    cy.login()
    cy.visit('/projects/1/dashboards/')
    cy.contains('You have no dashboards yet')
  })

  it('create, rename, and delete dashboard', () => {
    cy.contains('create one').click()
    cy.contains('This dashboard needs some widgets!')
    cy.get('input[value=Untitled]').clear().type("Marauder's Map{enter}")
    cy.get(`input[value="Marauder's Map"]`)
    cy.visit('/projects/1/dashboards/')
    cy.contains("Marauder's Map").click()
    cy.get('span[data-popover-target=trigger]').click()
    cy.contains('Yes').click()
    cy.contains('You have no dashboards yet')
  })

  it('create dashboard with two widgets', () => {
    cy.contains('create one').click()
    createWidget('Table')
    cy.contains('Save & Preview').should('not.be.disabled').click()
    cy.contains('Edinburgh')
    cy.get('button[name=close]').click({ force: true })
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

  it('duplicates dashboard with new widgets', () => {
    // Duplicates a dashboard with a table widget
    // Then changes the widget kind and checks whether the original
    // widget hasn't changed
    // TODO: Maybe add test for widget relations like filters or values
    cy.contains('create one').click()
    createWidget('Table')
    cy.contains('Save & Close').should('not.be.disabled').click()

    cy.visit('/projects/1/dashboards/')
    cy.get(`#dashboard-duplicate-${dashboardStartId}`).click()
    cy.contains('Copy of Untitled').click()
    cy.contains('Blackpool', { timeout: BIGQUERY_TIMEOUT })

    // TODO: trigger the hover and remove the force click
    // cy.get('#widgets-output-2').trigger('mouseover')
    cy.get(`#widget-update-${widgetStartId + 1}`).click({ force: true })
    cy.get('select-visual').find('button').click()
    cy.get('select-visual').contains('Column').click()
    cy.get('select[name=dimension]').select('Location')
    cy.get('[data-formset-prefix-value=aggregations]').within((el) => {
      cy.wrap(el).get('button').click()
    })
    cy.get('select[name=aggregations-0-column]').select('store_id')
    cy.get('select[name=aggregations-0-function]').select('MEAN')
    cy.contains('Save & Close').click()

    cy.visit('/projects/1/dashboards/')
    cy.contains(/^Untitled$/).click()
    cy.contains('Alex', { timeout: BIGQUERY_TIMEOUT })
  })

  it('shares a dashboard with a widget', () => {
    cy.contains('create one').click()
    createWidget('Table')
    cy.contains('Save & Close').should('not.be.disabled').click()
    cy.logout()

    cy.visit(`/projects/1/dashboards/${dashboardStartId}`)
    cy.location('pathname').should('equal', '/login/')

    cy.login()
    cy.visit(`/projects/1/dashboards/${dashboardStartId}`)
    cy.get(`#dashboard-share-${dashboardStartId}`).click()
    cy.get('button').contains('Share').click()

    cy.contains(
      /localhost:8000\/dashboards\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/
    )
      .invoke('text')
      .then((text) => {
        const sharedUrl = `http://${text.trim()}`
        cy.logout()

        cy.visit(sharedUrl)
        cy.contains('David')

        cy.login()
        cy.visit(`/projects/1/dashboards/${dashboardStartId}`)
        cy.get(`#dashboard-share-${dashboardStartId}`).click()
        cy.get('button').contains('Unshare').click()
        cy.get('.fa-link')
        cy.logout()

        // cy.visit fails on 404 by default
        cy.visit(sharedUrl, { failOnStatusCode: false })
        cy.contains('404 - Not Found')
      })
  })

  it('created workflow shows in dashboard', () => {
    const id = getModelStartId('nodes.node')

    cy.visit('/projects/1/workflows/')
    cy.contains('create one').click()
    cy.drag('#dnd-node-input')
    cy.drop('.react-flow')
    cy.get(`[data-id=${id}]`).dblclick()
    cy.contains('store_info').click()
    cy.contains('Save & Close').click()
    cy.reactFlowDrag(id, { x: 150, y: 300 })

    cy.drag('#dnd-node-output')
    cy.drop('[class=react-flow]')
    cy.get(`[data-id=${id + 1}]`).should('exist')
    cy.connectNodes(id, id + 1)
    cy.contains('Run').click()
    cy.contains('Last run')

    cy.visit('/projects/1/dashboards')
    cy.contains('create one').click()
    createWidget('Table')
    cy.get('select-source').find('button').click()
    cy.get('select-source').contains('Untitled - Untitled').click()

    cy.contains('Save & Preview').click()
    cy.contains('Loading widget...')
    cy.get(`#widgets-output-${widgetStartId} table`).contains('Edinburgh').should('be.visible')
  })
})
