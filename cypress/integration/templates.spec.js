/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const projectId = getModelStartId('projects.project')
const templateInstanceId = getModelStartId('templates.templateinstance')

describe('templates', () => {
  beforeEach(() => {
    cy.login()
    cy.visit('/teams/1')
  })
  it('new project from template', () => {
    cy.contains('Templates').click()
    cy.url().should('contain', '/teams/1/templates')

    // choose the template
    cy.contains('Google Analytics').click()

    // template preview loads
    cy.contains('Google Analytics')
    cy.contains('Bounce rate and session duration')
    cy.contains('avg_session_duration')

    // create the project with the template
    cy.get('button[type=submit]').click()
    cy.url().should('contain', `/projects/${projectId}/templates/${templateInstanceId}`)

    // setup the new Google Analytics connector, and it redirects back
    cy.get('#main').within(() => cy.contains('Setup').click())
    cy.get('button[type=submit]').click()
    cy.contains('continue').click()
    cy.get('button[type=submit]').click()
    cy.contains('Confirm', { timeout: 10000 }).click()
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
    // cy.contains('Yes').click()
    // cy.get('table tbody tr').should('have.length', 0)

    // cy.logout()
    // cy.login()
    // cy.visit(`/projects/${projectId}`)
    // cy.contains('Dashboard').click()
    // cy.contains('Basic metrics').click()

    // // dashboard still loads
    // cy.contains('Google Analytics')
    // cy.contains('Bounce rate and session duration')
    // cy.contains('avg_session_duration')
  })
})
