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

    cy.url().should('contain', '/projects/1/integrations/3/setup')
    cy.contains('Validating and importing your file...')
    cy.contains('File successfully validated and imported.', { timeout: 10000 })

    // review the table and approve
    cy.contains('London')
    cy.contains('Approve').click()

    // bigquery file upload needs longer wait
    cy.contains('Structure', { timeout: 10000 })
    cy.contains('Data')
    cy.contains('15')

    cy.url().should('contain', '/projects/1/integrations/3')
    // file name inferred
    cy.get('input[name=name]').should('have.value', 'store_info')

    // cannot edit upload setup
    cy.contains('Setup').should('not.exist')

    // check email sent
    cy.outbox()

      .then((outbox) => outbox.count)
      .should('eq', 1)
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
    cy.contains('Approve', { timeout: 20000 }).click()
    cy.contains('Structure')
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
  it('runtime failures', () => {
    cy.visit('/projects/1/integrations/uploads/new')

    // bigquery does not allow quoted newlines unless explicitly set
    cy.get('input[type=file]').attachFile('store_info_quoted_newlines.csv')
    cy.contains(
      'Error while reading data, error message: Error detected while parsing row starting at position: 52. Error: Missing close double quote (") character.',
      { timeout: 10000 }
    )
  })
})
