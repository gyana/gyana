/// <reference types="cypress" />

describe('sign up', () => {
  beforeEach(() => {
    // reset and seed the database prior to every test
    // explicit path required https://stackoverflow.com/a/55295044/15425660
    cy.exec('./.venv/bin/python manage.py flush --settings gyana.settings.test --noinput')
    cy.exec(
      './.venv/bin/python manage.py loaddata --settings gyana.settings.test cypress/fixtures/fixtures.json'
    )
  })

  it('signs up to app', () => {
    cy.visit('/')

    cy.contains('create one here!').click()
    cy.url().should('contain', '/accounts/signup')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('input[type=password]').type('seewhatmatters')

    cy.contains('Create Account').click()
    cy.url().should('contain', '/teams/new')

    cy.get('input[type=text]').type('Gyana')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/1')
  })
})
