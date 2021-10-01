/// <reference types="cypress" />

const NOT_REDEEMED = '12345678'

import { getModelStartId } from '../support/utils'

const newTeamId = getModelStartId('teams.team')

describe('appsumo', () => {
  it('signup with code', () => {
    cy.visit(`/appsumo/${NOT_REDEEMED}`)

    cy.url().should('contain', `/appsumo/signup/${NOT_REDEEMED}`)
    cy.contains('AppSumo code')
    cy.get(`input[value=${NOT_REDEEMED}]`).should('be.disabled')

    cy.get('input[name=email]').type('appsumo@gyana.com')
    cy.get('input[name=password1]').type('seewhatmatters')
    cy.get('input[name=team]').type('Teamsumo')
    cy.get('button[type=submit]').click()

    // remove message blocking the form
    cy.get('.fa-times').first().click()
    // onboarding
    cy.get('input[name=first_name]').type('Appsumo')
    cy.get('input[name=last_name]').type('User')
    cy.contains('Next').click()

    cy.get('select[name=company_industry]').select('Agency')
    cy.get('select[name=company_role]').select('Marketing')
    cy.get('select[name=company_size]').select('2-10')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', `/teams/${newTeamId}`)
  })
})
