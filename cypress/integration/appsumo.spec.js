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
    cy.contains(
      `This code (${REDEEMED_BY_ANOTHER_USER}) has already been redeemed by another user.`
    )
    cy.contains('contact support@gyana.com for support.')

    // code already redeemed by you
    cy.logout()
    cy.login('test@gyana.com')

    cy.visit(`/appsumo/${REDEEMED_BY_USER}`)
    cy.contains(`You've already redeemed the code ${REDEEMED_BY_USER}`)
    cy.contains('your account for').click()
    cy.url().should('contain', 'teams/1/account')
  })
  it('landing', () => {
    cy.visit('/appsumo')

    // code does not exist
    cy.get('input[name=code]').type(NOT_EXIST)
    cy.get('button[type=submit]').click()

    cy.contains('AppSumo code does not exist')

    // code exists
    cy.get('input[name=code]').clear().type(NOT_REDEEMED)
    cy.get('button[type=submit]').click()

    cy.url().should('contain', `/appsumo/signup/${NOT_REDEEMED}`)
  })
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
  it('redeem code on existing account and teams', () => {
    cy.login()
    cy.visit(`/appsumo/${NOT_REDEEMED}`)

    cy.url().should('contain', `/appsumo/redeem/${NOT_REDEEMED}`)
    cy.contains(`Reedem AppSumo code ${NOT_REDEEMED}.`)

    cy.get('select[name=team]').select('Vayu')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams')
  })
  it('redeem code on existing account and no teams', () => {
    cy.login('alone@gyana.com')
    cy.visit(`/appsumo/${NOT_REDEEMED}`)

    cy.url().should('contain', `/appsumo/redeem/${NOT_REDEEMED}`)
    cy.contains(`Reedem AppSumo code ${NOT_REDEEMED}.`)

    cy.get('input[name=team_name]').type('New team')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams')
  })
  it('stack and refund including credits', () => {
    cy.login()

    cy.visit('/teams/1/account')
    cy.contains('Stack Code').click()
    cy.get('input[name=code]').type(NOT_REDEEMED)
    cy.get('button[type=submit]').click()

    cy.get('#appsumo-list table tbody tr').should('have.length', 2)
    // check deal information
    cy.contains('Final deal $59 (01/07/21 - 26/08/21)')
    cy.contains('Launch deal $49 (24/03/21 - 25/06/21)')

    cy.visit('/teams/1/account')
    // 2 codes = 2M rows
    cy.contains('0 / 2,000,000')
    // 2 codes = 20k credits
    cy.contains('20,000')

    // refund a code
    cy.logout()
    cy.login('admin@gyana.com')
    cy.visit('/admin/appsumo/refundedcodes/add')
    cy.get('input[type=file]').attachFile('appsumo_refunded.csv')
    cy.get('input[name=downloaded_0]').type('2021-08-24')
    cy.get('input[name=downloaded_1]').type('00:00:00')
    cy.get('input[value=Save]').click({ turbo: false })

    cy.logout()
    cy.login()

    cy.visit('/teams/1/account')
    // 1 active codes = 1M rows
    cy.contains('0 / 1,000,000')
    // 1 code = 10k credits
    cy.contains('10,000')
  })
  it('link to review', () => {
    cy.login()

    // enter the review

    cy.visit('/teams/1/account')
    cy.contains('Link to your review').click()

    cy.url().should('contain', '/teams/1/appsumo/review')
    cy.get('input[name=review_link]').type(
      'https://appsumo.com/products/marketplace-gyana/#r000000'
    )
    cy.get('button[type=submit]').click()

    cy.contains('Thank you for writing an honest review!')

    // they get an extra code

    cy.visit('/teams/1/account')
    cy.contains('2,000,000')

    // cannot use review twice

    cy.visit('/teams/2/appsumo/review')
    cy.get('input[name=review_link]').type(
      'https://appsumo.com/products/marketplace-gyana/#r000000'
    )
    cy.get('button[type=submit]').click()

    cy.contains(
      "If you think this is a mistake, reach out to support and we'll sort it out for you."
    )
  })
  it('admin extra rows', () => {
    cy.login()
    cy.visit('/teams/1/account')
    cy.contains('1,000,000')

    // apply the extra rows
    cy.logout()
    cy.login('admin@gyana.com')
    cy.visit('/admin/teams/team/1/change')
    cy.get('input[name=appsumoextra_set-0-rows]').type('2000000')
    cy.get('textarea[name=appsumoextra_set-0-reason]').type('For being awesome')
    cy.contains('Save').click({ turbo: false })
    cy.logout()

    cy.login()
    cy.visit('/teams/1/account')
    cy.contains('3,000,000')

    cy.contains('AppSumo').click()
    cy.contains('For being awesome')
  })
})
