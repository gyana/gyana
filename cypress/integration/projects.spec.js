/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const newProjectUrl = `/projects/${getModelStartId('projects.project')}`

describe('projects', () => {
  beforeEach(() => {
    cy.login()
  })
  it('create, read, update, delete and list', () => {
    cy.visit('/')

    // create

    cy.contains('New Project').click()

    cy.url().should('contain', '/teams/1/projects/new')
    cy.get('input[name=name]').type('Metrics')
    cy.get('textarea[name=description]').type('All the company metrics')
    cy.get('button[type=submit]').click()

    // read

    cy.url().should('contain', newProjectUrl)
    cy.contains('Metrics')
    cy.contains('All the company metrics')

    // list

    cy.get('#sidebar a').first().click()
    cy.url().should('contain', '/teams/1')
    cy.get('table tbody tr').should('have.length', 3)
    cy.contains('Metrics').click()

    // update

    cy.contains('Settings').click()

    cy.url().should('contain', newProjectUrl + '/update')
    cy.get('input[name=name]').clear().type('KPIs')
    cy.get('textarea[name=description]').clear().type('All the company kpis')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', newProjectUrl)
    cy.contains('KPIs')
    cy.contains('All the company kpis')

    // delete

    cy.contains('Settings').click()
    cy.contains('Delete').click()
    cy.contains('Yes').click()

    cy.url().should('contain', '/teams/1')
    cy.get('table tbody tr').should('have.length', 2)
    cy.contains('Metrics').should('not.exist')
  })
})
