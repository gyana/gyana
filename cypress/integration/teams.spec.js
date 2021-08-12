/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const newTeamId = getModelStartId('teams.team')

describe('teams', () => {
  beforeEach(() => {
    cy.login()
  })
  it('create, read, update and delete', () => {
    cy.visit('/')

    cy.get('#heading').within(() => cy.contains('Vayu'))

    // create
    cy.get('#sidebar-newteam').click()
    cy.url().should('contain', '/teams/new')

    cy.get('input[type=text]').type('Neera')
    cy.get('button[type=submit]').click()

    // view
    const newTeamUrl = `/teams/${newTeamId}`
    cy.url().should('contain', newTeamUrl)
    cy.get('#heading').within(() => cy.contains('Neera'))

    // switch
    cy.get('#sidebar').within(() => {
      cy.contains('Vayu').click()
    })
    cy.url().should('contain', '/teams/1')
    cy.get('#sidebar').within(() => {
      cy.contains('Neera').click()
    })
    cy.url().should('contain', newTeamUrl)

    // update
    cy.contains('Settings').click()
    cy.url().should('contain', newTeamUrl + '/update')
    cy.get('input[type=text]').clear().type('Agni')
    cy.get('button[type=submit]').click()
    cy.get('#heading').within(() => cy.contains('Agni'))

    // delete
    cy.contains('Delete').click()
    cy.url().should('contain', newTeamUrl + '/delete')
    cy.get('button[type=submit]').click()
    cy.get('#sidebar').contains('Agni').should('not.exist')
  })
  it('change member role and check restricted permissions', () => {
    cy.visit('/')

    cy.contains('Members').click()

    cy.contains('member@gyana.com').click()

    cy.get('select').select('Member')
    cy.get('button[type=submit]').click()

    cy.logout()
    cy.login('member@gyana.com', 'seewhatmatters')

    cy.visit('/')

    cy.wrap(['Members', 'Invites', 'Settings']).each((page) =>
      cy.contains(page).should('not.exist')
    )

    cy.wrap(['members', 'invites', 'update']).each((url) => {
      cy.request({ url: `/teams/1/${url}`, failOnStatusCode: false })
        .then((response) => response.status)
        .should('eq', 404)
    })
  })
  it('remove member', () => {
    cy.visit('/teams/1/members')

    cy.contains('member@gyana.com').click()

    cy.contains('Delete').click()
    cy.contains('Yes').click()

    cy.contains('member@gyana.com').should('not.exist')

    cy.logout()
    cy.login('member@gyana.com', 'seewhatmatters')

    cy.visit('/')
    cy.contains('Vayu').should('not.exist')

    cy.request({ url: '/teams/1', failOnStatusCode: false })
      .then((response) => response.status)
      .should('eq', 404)
  })
})
