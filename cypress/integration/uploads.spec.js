/// <reference types="cypress" />

describe('uploads', () => {
  beforeEach(() => {
    cy.login()

    cy.visit('/projects/1/integrations')
  })
  it('upload valid CSV', () => {
    cy.contains('New Integration').click()
    cy.contains('Upload CSV').click()

    cy.url().should('contain', '/projects/1/integrations/uploads/new')
    cy.get('input[type=file]').attachFile('store_info.csv')
    cy.contains('File uploaded')
    cy.get('button[type=submit]').click()

    cy.url().should('contain', '/projects/1/integrations/uploads/2')
    cy.contains('Validating and importing your file...')
    cy.contains('File successfully validated and imported.')

    // // bigquery file upload needs longer wait
    cy.contains('Structure', { timeout: 10000 })
    cy.contains('Data')
    cy.contains('15')

    cy.url().should('contain', '/projects/1/integrations/3')
    // file name inferred
    cy.get('input[name=name]').should('have.value', 'store_info')

    // check email sent
    cy.outbox()
      .then((outbox) => outbox.count)
      .should('eq', 1)
  })
  it('streamed uploads with chunks', () => {
    cy.visit('/projects/1/integrations/uploads/new', {
      onBeforeLoad(window) {
        // the total file size is 345 bytes
        // requires 3 chunks to upload
        window.__cypressChunkSize__ = 128
      },
    })

    cy.get('input[type=file]').attachFile('store_info.csv')
    cy.contains('File uploaded')
    cy.get('button[type=submit]').click()

    cy.contains('Structure', { timeout: 10000 })
  })
  it('validation failures', () => {
    cy.contains('New Integration').click()
    cy.contains('Upload CSV').click()

    // need to upload file
    cy.get('button[type=submit]').click()
    cy.contains('This field is requied')

    //
  })
})
