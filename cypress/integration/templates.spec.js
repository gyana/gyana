/// <reference types="cypress" />

import { getModelStartId, BIGQUERY_TIMEOUT } from '../support/utils'

const projectId = getModelStartId('projects.project')
const templateInstanceId = getModelStartId('templates.templateinstance')

const checkDashboard = () => {
  // chart 1, google analytics
  // title
  cy.contains('Bounce rate and session duration')
  // axis
  cy.contains('avg_session_duration')
  // chart 2, upload
  // title
  cy.contains('Employees by owner')
  // axis
  cy.contains('Alex')
}

describe('templates', () => {
  beforeEach(() => {
    cy.login()
  })
  it('new project', () => {
    cy.visit('/teams/1')

    cy.contains('Create a new project')

    // choose the template
    cy.contains('Google Analytics').click()

    // template preview loads
    cy.contains('Google Analytics')
    checkDashboard()

    // create the project with the template
    cy.get('button[value=create]').click({ turbo: false })
    cy.url().should('contain', `/projects/${projectId}/templates/${templateInstanceId}`)

    // setup the new Google Analytics connector, and it redirects back
    cy.get('#main').within(() => cy.contains('Connect').click())
    cy.get('button[type=submit]').click()
    cy.contains('continue').click()
    cy.get('button[type=submit]').click()
    cy.contains('Confirm', { timeout: BIGQUERY_TIMEOUT }).click()
    cy.url().should('contain', `/projects/${projectId}/templates/${templateInstanceId}`)

    // finish setup and run all duplication logic
    cy.get('button[type=submit]').click()
    cy.url().should('contain', `/projects/${projectId}`)

    // go and delete the old project
    cy.logout()
    cy.login('admin@gyana.com')
    cy.visit('/')
    cy.contains('Google Analytics').click()
    cy.contains('Settings').click()
    cy.contains('Delete').click()
    cy.contains('Yes').click()
    cy.get('table tbody tr').should('have.length', 0)

    cy.logout()
    cy.login()
    cy.visit(`/projects/${projectId}`)
    cy.contains('Dashboard').click()
    cy.contains('Basic metrics').click()

    // dashboard still loads
    checkDashboard()
  })
  it('existing project', () => {
    cy.visit('/projects/1/integrations')

    // setup a project with Google Analytics
    // from connectors.spec.js

    cy.contains('New Integration').click()
    cy.contains('New Connector').click()
    cy.contains('Google Analytics').click()
    cy.get('button[type=submit]').click()
    cy.contains('continue').click()
    cy.get('button[type=submit]').click()
    cy.contains('Confirm', { timeout: BIGQUERY_TIMEOUT }).click()

    // add template to project
    cy.visit('/teams/1')
    cy.contains('Google Analytics').click()
    cy.get('#templates-add').click()
    cy.get('select').select('Cypress test project')
    cy.get('button[value=add]').click()

    // we can navigate to other parts of the project and come back
    cy.get('#sidebar').within(() => cy.contains('Integrations').click())
    cy.contains('Setup').click()
    cy.contains('Google Analytics').click()

    // uses existing connector
    cy.get('.fa-check-circle')
    cy.get('button[type=submit]').click()

    // dashboard loads
    cy.contains('Dashboard').click()
    cy.contains('Basic metrics').click()
    checkDashboard()
  })
})
