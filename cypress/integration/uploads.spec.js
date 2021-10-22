/// <reference types="cypress" />

import { getModelStartId, BIGQUERY_TIMEOUT } from '../support/utils'
const id = getModelStartId('integrations.integration')

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

    cy.url().should('contain', `/projects/1/integrations/${id}/configure`)
    cy.get('button[type=submit]').click()
    cy.contains('Validating and importing your upload...')
    cy.contains('Upload successfully validated and imported.', { timeout: BIGQUERY_TIMEOUT })

    // review the table and approve
    cy.contains('preview').click()
    cy.contains('Employees')
    cy.contains('Setup').click()
    cy.contains('Confirm').click()

    // bigquery file upload needs longer wait
    cy.contains('Data', { timeout: BIGQUERY_TIMEOUT })
    cy.contains('Overview')
    // validate row count
    cy.contains('15')

    cy.url().should('contain', `/projects/1/integrations/${id}`)
    // file name inferred
    cy.get('input[name=name]').should('have.value', 'store_info')

    // cannot edit upload setup
    cy.contains('Setup').should('not.exist')
  })
  it('streamed uploads with chunks', () => {
    cy.visit('/projects/1/integrations/uploads/new', {
      onBeforeLoad(window) {
        // minimum chunk size allowed "a multiple of 256 KiB (256 x 1024 bytes)"
        // https://cloud.google.com/storage/docs/performing-resumable-uploads#chunked-upload
        // by construction file is 1.1 MB = 2 chunks
        window.__cypressChunkSize__ = 512 * 1024
      },
    })

    cy.get('input[type=file]').attachFile('fifa.csv')

    // wait for entire process to happen successfully
    cy.get('button[type=submit]').click()
    cy.contains('Confirm', { timeout: BIGQUERY_TIMEOUT }).click()
    cy.contains('Data')
    // 2250 lines of CSV including header
    cy.contains(2249)
  })
  it('upload failures', () => {
    // invalid format - better way to test this?
    cy.visit('/projects/1/integrations/uploads/new')
    cy.get('input[type=file]').invoke('attr', 'accept').should('eq', '.csv')

    // file is too large
    cy.visit('/projects/1/integrations/uploads/new', {
      onBeforeLoad(window) {
        // store_info is 345 bytes
        window.__cypressMaxSize__ = 128
      },
    })

    cy.get('input[type=file]').attachFile('store_info.csv')
    cy.contains('Errors occurred when uploading your file')
    cy.contains('This file is too large')

    // upload errors e.g. bad connectivity or Google is down
    cy.visit('/projects/1/integrations/uploads/new', {
      onBeforeLoad(window) {
        window.__cypressMaxBackoff__ = 1
      },
    })
    cy.intercept(
      { method: 'PUT', url: 'https://storage.googleapis.com/gyana-local/**/*' },
      { statusCode: 500 }
    )

    cy.get('input[type=file]').attachFile('store_info.csv')
    cy.contains('Errors occurred when uploading your file')
    cy.contains('Server error, try again later')
  })
})
