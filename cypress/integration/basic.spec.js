/// <reference types="cypress" />

describe('sign up', () => {
  beforeEach(() => {
    // reset and seed the database prior to every test
    // explicit path required https://stackoverflow.com/a/55295044/15425660
    cy.exec('./.venv/bin/python manage.py cypress_reset')
  })

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
