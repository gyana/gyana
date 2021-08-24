/// <reference types="cypress" />

const NOT_EXIST = '00000000'
const NOT_REDEEMED = '12345678'
const REDEEMED_BY_USER = 'ABCDEFGH'
const REDEEMED_BY_ANOTHER_USER = 'QWERTYUI'

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
})
