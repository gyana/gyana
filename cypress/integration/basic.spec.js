/// <reference types="cypress" />

describe('sign up', () => {
  it('signs up to app', () => {
    cy.visit('http://localhost:8000')

    cy.contains('create one here!').click()
    cy.url().should('contain', '/accounts/signup')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('input[type=password]').type('seewhatmatters')

    cy.contains('Create Account').click()
  })
})
