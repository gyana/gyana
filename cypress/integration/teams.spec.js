/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const newTeamId = getModelStartId('teams.team')

describe('teams', () => {
  beforeEach(() => {
    cy.login()
  })
  it('create, read, update and delete', () => {
    // redirect to the most recently created team
    cy.visit('/')
    cy.url().should('contain', `/teams/4`)

    // now start test
    cy.visit('/teams/1')

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
    cy.contains('Team deletion is disabled')
    cy.get('button').contains('Delete').should('be.disabled')
    // cy.contains('Delete').click()
    // cy.url().should('contain', newTeamUrl + '/delete')
    // cy.get('button[type=submit]').click()
    // cy.get('#sidebar').contains('Agni').should('not.exist')
  })
  it('change member role and check restricted permissions', () => {
    cy.visit('/teams/1')

    cy.contains('Members').click()

    cy.contains('member@gyana.com').click()

    cy.get('select').select('Member')
    cy.get('button[type=submit]').click()

    cy.logout()
    cy.login('member@gyana.com', 'seewhatmatters')

    cy.visit('/')

    cy.wrap(['Members', 'Billing', 'Settings']).each((page) =>
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

    cy.get('a').contains('Delete').click()
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
  it('account limit warning', () => {
    cy.visit('/')

    // special team with warning amount
    cy.contains('Warning').click()

    // initially the row_count was not updated
    cy.contains("You've exceeded your row count limit.").should('not.exist')
    // periodic job to calculate this information
    cy.periodic()
    cy.reload()

    cy.contains("You're exceeding your row count limit.")

    // now we go and delete that data source
    cy.get('#main').within(() => cy.contains('Warning').click())
    cy.contains('1 upload').click()
    cy.contains('store_info').click()
    cy.get('#tabbar').within(() => cy.contains('Settings').click())
    cy.get('a').contains('Delete').click()
    cy.contains('Yes').click()

    cy.visit('/')
    cy.contains('Warning').click()
    cy.get('nav').contains('Billing').click()
    // row count automatically updated when integration deleted
    cy.contains("You're exceeding your row count limit.").should('not.exist')
  })
  it('account limit disabled', () => {
    cy.visit('/')

    // special account with disabled amount
    cy.contains('Disabled').click()
    cy.contains(
      "You've exceeded your row count limit by over 20%, your team is temporarily disabled."
    )

    cy.contains('Learn more').click()
    cy.contains('15 / 10')

    // check disabled
    cy.contains('Projects').click()
    cy.get('#main').within(() => cy.contains('Disabled').click())

    // cannot create a new integration
    cy.contains('Integrations').click()
    cy.contains('New Integration').should('be.disabled')
  })
})
