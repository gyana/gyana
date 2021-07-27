/// <reference types="cypress" />

describe('sign up', () => {
  it('signs in headlessly', () => {
    cy.login()

    cy.visit('/')
  })

  it('signs up to app', () => {
    cy.visit('/accounts/signup')

    cy.get('input[type=email]').type('new@gyana.com')
    cy.get('input[type=password]').type('seewhatmatters')

    cy.contains('Create Account').click()
    cy.url().should('contain', '/teams/new')

    cy.get('input[type=text]').type('New')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/2')
  })
})
