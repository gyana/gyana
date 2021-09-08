/// <reference types="cypress" />

import { getModelStartId } from '../support/utils'

const newTeamId = getModelStartId('teams.team')

describe('users', () => {
  it('signs in to app', () => {
    cy.visit('/')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('input[type=password]').type('seewhatmatters')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/teams/4')
  })

  it('signs up to app with onboarding', () => {
    cy.visit('/accounts/signup')
    cy.contains('Sign Up Closed')

    // signup is disabled, uncomment when freemium is live

    // cy.contains('create one here').click()
    // cy.url().should('contain', '/accounts/signup')

    // cy.get('input[type=email]').type('new@gyana.com')
    // cy.get('input[type=password]').type('seewhatmatters')
    // cy.get('button[type=submit]').click()
    // cy.url().should('contain', '/users/onboarding')

    // // remove message blocking the form
    // cy.get('.fa-times').first().click()
    // // onboarding
    // // cy.get('input[name=first_name]').type('New')
    // // cy.get('input[name=last_name]').type('User')
    // cy.get('select[name=company_industry]').select('Agency')
    // cy.get('select[name=company_role]').select('Marketing')
    // cy.get('select[name=company_size]').select('2-10')
    // cy.get('button[type=submit]').click()
    // cy.url().should('contain', '/teams/new')

    // cy.get('input[type=text]').type('New')
    // cy.get('button[type=submit]').click()
    // cy.url().should('contain', `/teams/${newTeamId}`)

    // // verification email
    // cy.outbox()
    //   .then((outbox) => outbox.count)
    //   .should('eq', 1)

    // cy.outbox().then((outbox) => {
    //   const msg = outbox['messages'][0]
    //   const url = msg['payload']
    //     .split('\n')
    //     .filter((x) => x.includes('http'))[0]
    //     .replace('To confirm this is correct, go to ', '')

    //   cy.visit(url)

    //   cy.contains('You have confirmed new@gyana.com')
    // })
  })

  it('resets password', () => {
    cy.visit('/')

    cy.contains('Forgot your password?').click()
    cy.url().should('contain', '/accounts/password/reset')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('button[type=submit]').click()
    cy.url().should('contain', '/accounts/password/reset/done')

    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)

    cy.outbox().then((outbox) => {
      const msg = outbox['messages'][0]
      const url = msg['payload'].split('\n').filter((x) => x.startsWith('http'))[0]
      cy.visit(url)
    })
    cy.url().should('contain', 'accounts/password/reset/key/1-set-password')

    cy.get('input[type=password]').first().type('senseknowdecide')
    cy.get('input[type=password]').last().type('senseknowdecide')
    cy.get('input[type=submit]').click()
    cy.url().should('contain', 'accounts/password/reset/key/done')

    cy.visit('/')

    cy.get('input[type=email]').type('test@gyana.com')
    cy.get('input[type=password]').type('senseknowdecide')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', `/teams/4`)
  })

  it('signs out', () => {
    cy.login()

    cy.visit('/')

    cy.get('#sidebar-profile').click()
    cy.url().should('contain', '/users/profile')

    cy.contains('Sign out').click()

    cy.url().should('contain', '/accounts/login')

    cy.visit('/users/profile')

    cy.url().should('contain', '/accounts/login')
  })
})
