/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const newProjectUrl = `/projects/${getModelStartId('projects.project')}`

const newTeamId = getModelStartId('teams.team')

describe('signup', () => {
  it('signup from website', () => {
    cy.visit('/signup')
    cy.get('input[name=email]').type('new@gyana.com')
    cy.get('input[name=password1]').type('seewhatmatters')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/confirm-email/')

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][0]
      // payload[0] is txt, payload[1] is html
      const url = msg['payload'][0].match(/\bhttps?:\/\/\S+/gi)[0]
      cy.visit(url)
    })

    // onboarding
    cy.get('input[name=first_name]').type('Waitlist')
    cy.get('input[name=last_name]').type('User')
    cy.get('input[name=marketing_allowed][value=True]').click()
    cy.contains('Next').click()

    cy.get('select[name=company_industry]').select('Agency')
    cy.get('select[name=company_role]').select('Marketing')
    cy.get('select[name=company_size]').select('2-10')
    cy.get('button[type=submit]').click()

    // new team
    cy.url().should('contain', '/teams')
    cy.get('input[name=name]').type('My team')
    cy.get('button[type=submit]').click({ turbo: false })

    // select plan and continue
    cy.url().should('contain', `/teams/${newTeamId}/plans`)
    cy.contains('Continue').click()

    // new project
    cy.url().should('contain', `/teams/${newTeamId}`)
    cy.contains('Create a new project').click()

    cy.url().should('contain', `/teams/${newTeamId}/projects/new`)
    cy.get('input[name=name]').type('Metrics').blur()
    cy.get('textarea[name=description]').should('not.be.disabled')
    cy.get('textarea[name=description]').type('All the company metrics')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', newProjectUrl)
    cy.contains('Metrics')
    cy.contains('All the company metrics')
  })
})
