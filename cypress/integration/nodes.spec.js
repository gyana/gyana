/// <reference types="cypress" />
const { _ } = Cypress

const openModalAndCheckTitle = (id, title) => {
  cy.visit(`/projects/2/workflows/1?modal_item=${id}`)
  cy.get('#node-editable-title').find(`[value="${title}"]`)
}

const testHelp = (text) => {
  cy.get('[class=tabbar]').contains('Help').click()
  cy.contains(text)
}

const addFormToFormset = (formset) => {
  cy.get(`[data-formset-prefix-value=${formset}]`).within((el) => {
    cy.wrap(el).get('button').click()
  })
}
const getFirstColumn = (rows$) => _.map(rows$, (el$) => el$.querySelectorAll('td')[0])
const toStrings = (cells$) => _.map(cells$, 'textContent')
const toNumbers = (texts) => _.map(texts, Number)

describe('workflows', () => {
  beforeEach(() => {
    cy.login('nodes@gyana.com')
  })

  it('Input', () => {
    openModalAndCheckTitle(19, 'Get data')

    cy.contains('revenue')
    cy.contains('store_info').click()
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...')
    cy.contains('Edinburgh')

    cy.contains('revenue').click()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'Edinburgh')
    cy.contains('100000')
  })

  it('Output', () => {
    openModalAndCheckTitle(2, 'Save data')

    cy.contains('Edinburgh')
    cy.get('input[name=output_name]')
      .should('have.value', '')
      .type('Naturalis Principia Mathematica')
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...')
    cy.contains('Edinburgh')
    cy.get('input[name=output_name]').should('have.value', 'Naturalis Principia Mathematica')
  })

  it('Select', () => {
    openModalAndCheckTitle(3, 'Select columns')

    testHelp('Use the select node')
    cy.contains('Owner').click()
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...')
    cy.contains('David')
    cy.get('#workflows-grid').should('not.contain', 'Edinburgh')

    cy.contains('Employees').click()
    cy.contains('Save & Preview').click()
    cy.contains('15')
    cy.get('select[name=select_mode]').should('have.value', 'keep').select('exclude')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'David')
    cy.contains('Edinburgh')
  })

  it('Aggregation', () => {
    openModalAndCheckTitle(4, 'Aggregation')

    testHelp('Aggregations are useful to generate')
    cy.get('#node-update-form').contains('Aggregations')
    cy.get('#node-update-form').contains('Columns')

    addFormToFormset('columns')
    cy.get('select[name=columns-0-column]').should('have.value', '').select('Location')
    cy.contains('Save & Preview').click()
    cy.contains('count')
    cy.contains('5')

    addFormToFormset('aggregations')
    cy.get('select[name=aggregations-0-column]').should('have.value', '').select('Employees')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'count')
    cy.get('#workflows-grid').contains('45')

    cy.get('select[name=aggregations-0-function]').select('MEAN')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', '45')
    cy.get('#workflows-grid').contains('9.0')

    cy.get('select[name=aggregations-0-column]').select('Owner')
    cy.get('select[name=aggregations-0-function]')
      .should('not.contain', 'MEAN')
      .should('have.value', 'count')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'count')
    cy.get('#workflows-grid').contains('5')

    // TODO: Test formset deletion
  })

  it('Sort', () => {
    openModalAndCheckTitle(5, 'Sort')
    cy.contains('Sort columns')
    testHelp('Sort the table based')
    addFormToFormset('sort_columns')
    cy.get('select[name=sort_columns-0-column]').should('have.value', '').select('store_id')
    cy.contains('Save & Preview').click()

    cy.get('#workflows-grid tbody').within(() => {
      cy.get('tr')
        .then(getFirstColumn)
        .then(toStrings)
        .then(toNumbers)
        .then((values) => {
          const sorted = _.sortBy(values)
          expect(values).to.deep.equal(sorted)
        })
    })

    cy.get('input[name=sort_columns-0-ascending').click()
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...')

    cy.get('#workflows-grid tbody').within(() => {
      cy.get('tr')
        .then(getFirstColumn)
        .then(toStrings)
        .then(toNumbers)
        .then((values) => {
          const sorted = _.reverse(_.sortBy(values))
          expect(values).to.deep.equal(sorted)
        })
    })
  })
  it('Limit', () => {
    openModalAndCheckTitle(6, 'Limit')
    testHelp('Limits the rows to the selected')
    cy.contains('Offset')

    cy.contains('Result').click()
    cy.get('#workflows-grid tbody tr').should('have.length', 15)
    cy.get('input[name=limit_limit]').clear().type(5)
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid tbody tr').should('have.length', 5)
    cy.get('#workflows-grid').contains('Floris')

    cy.get('input[name=limit_offset]').type(3)
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'Floris')
    cy.get('#workflows-grid tbody tr').should('have.length', 5)
  })
})
