/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const NOT_REDEEMED = '12345678'

const newProjectUrl = `/projects/${getModelStartId('projects.project')}`

const newTeamId = getModelStartId('teams.team')

describe('signup', () => {
  it('signup with code', () => {
    cy.visit(`/appsumo/${NOT_REDEEMED}`)

    cy.url().should('contain', `/appsumo/signup/${NOT_REDEEMED}`)
    cy.contains('AppSumo code')
    cy.get(`input[value=${NOT_REDEEMED}]`).should('be.disabled')

    cy.get('input[name=email]').type('appsumo@gyana.com')
    cy.get('input[name=password1]').type('seewhatmatters')
    cy.get('input[name=team]').type('Teamsumo')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/confirm-email/')

    cy.wait(1000)

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][0]
      // payload[0] is txt, payload[1] is html
      const url = msg['payload'][0].match(/\bhttps?:\/\/\S+/gi)[0]
      cy.visit(url)
    })

    // onboarding
    cy.get('input[name=first_name]').type('Appsumo')
    cy.get('input[name=last_name]').type('User')
    cy.contains('Next').click()

    cy.get('select[name=company_industry]').select('Agency')
    cy.get('select[name=company_role]').select('Marketing')
    cy.get('select[name=company_size]').select('2-10')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', `/teams/${newTeamId}`)

    // new project
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
