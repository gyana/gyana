/// <reference types="cypress" />

const NOT_EXIST = '00000000'
const NOT_REDEEMED = '12345678'
const REDEEMED_BY_USER = 'ABCDEFGH'
const REDEEMED_BY_ANOTHER_USER = 'QWERTYUI'

import { getModelStartId } from '../support/utils'

const newTeamId = getModelStartId('teams.team')

describe('appsumo', () => {
  it('invalid codes', () => {
    // code does not exist
    cy.request({ url: `/appsumo/${NOT_EXIST}`, failOnStatusCode: false })
      .then((response) => response.status)
      .should('eq', 404)

    // code already redeemed by someone else
    cy.login('member@gyana.com')

    cy.visit(`/appsumo/${REDEEMED_BY_ANOTHER_USER}`)
    cy.contains(`Error, the code ${REDEEMED_BY_ANOTHER_USER} was already redeemed by another user.`)
    cy.contains('Contact support@gyana.com for support.')

    // code already redeemed by you
    cy.logout()
    cy.login('test@gyana.com')

    cy.visit(`/appsumo/${REDEEMED_BY_USER}`)
    cy.contains(`You've already redeem the code ${REDEEMED_BY_USER}`)
    cy.contains('your account for').click()
    cy.url().should('contain', 'teams/1/account')
  })
  it('signup with code', () => {
    cy.visit(`/appsumo/${NOT_REDEEMED}`)

    cy.url().should('contain', `/appsumo/signup/${NOT_REDEEMED}`)
    cy.contains(`Signup with AppSumo code ${NOT_REDEEMED}.`)

    cy.get('input[name=first_name]').type('Appsumo')
    cy.get('input[name=last_name]').type('User')
    cy.get('input[name=email]').type('appsumo@gyana.com')
    cy.get('input[name=password1]').type('seewhatmatters')
    cy.get('input[name=team]').type('Teamsumo')

    cy.get('button[type=submit]').click()

    cy.url().should('contain', `/teams/${newTeamId}`)
  })
  it('redeem code on existing account', () => {
    cy.login()
    cy.visit(`/appsumo/${NOT_REDEEMED}`)

    cy.url().should('contain', `/appsumo/redeem/${NOT_REDEEMED}`)
    cy.contains(`Reedem AppSumo code ${NOT_REDEEMED}.`)

    cy.get('select[name=team]').select('Vayu')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/1')
  })
})
