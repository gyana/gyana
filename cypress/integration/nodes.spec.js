/// <reference types="cypress" />
const { _ } = Cypress

const openModalAndCheckTitle = (id, title) => {
  cy.visit(`/projects/2/workflows/1?modal_item=${id}`)
  cy.get('#node-editable-title').find(`[value="${title}"]`)
}

const testHelp = (text) => {
  cy.get('[class=tabbar]').contains('Help').click()
  cy.contains(text).should('be.visible')
}

const addFormToFormset = (formset) => {
  cy.get(`[data-formset-prefix-value=${formset}]`).within((el) => {
    cy.wrap(el).get(`#${formset}-add`).click()
  })
}

const waitForLiveFormUpdate = () => {
  cy.get('[data-live-update-target=loading]').should('be.visible')
  cy.get('[data-live-update-target=loading]').should('not.be.visible')
}

const getFirstColumn = (rows$) => _.map(rows$, (el$) => el$.querySelectorAll('td')[0])
const toStrings = (cells$) => _.map(cells$, 'textContent')
const toNumbers = (texts) => _.map(texts, Number)

describe('nodes', () => {
  beforeEach(() => {
    cy.login('nodes@gyana.com')
  })

  it('Input', () => {
    openModalAndCheckTitle(19, 'Get data')

    cy.contains('revenue')
    cy.get('#node-update-form').contains('store_info').should('be.visible').click()
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...').should('be.visible')
    cy.contains('Edinburgh').should('be.visible')

    cy.contains('revenue').click()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'Edinburgh')
    cy.contains('100000').should('be.visible')

    testHelp('Select data from an integration to be used in your workflow.')
  })

  it('Output', () => {
    openModalAndCheckTitle(2, 'Save data')
    cy.contains('Edinburgh')
    testHelp("The connected nodes' data will be available to be")

    cy.get('input[name=output_name]')
      .should('have.value', '')
      .type('Naturalis Principia Mathematica')
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...').should('be.visible')
    cy.contains('Edinburgh').should('be.visible')
    cy.get('input[name=output_name]').should('have.value', 'Naturalis Principia Mathematica')
  })

  it('Select', () => {
    openModalAndCheckTitle(3, 'Select columns')
    testHelp('Use the select node')

    cy.contains('Owner').click()
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...').should('be.visible')
    cy.contains('David').should('be.visible')
    cy.get('#workflows-grid').should('not.contain', 'Edinburgh')

    cy.contains('Employees').click()
    cy.contains('Save & Preview').click()
    cy.contains('15').should('be.visible')
    cy.get('select[name=select_mode]').should('have.value', 'keep').select('exclude')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'David')
    cy.contains('Edinburgh').should('be.visible')
  })

  it('Aggregation', () => {
    openModalAndCheckTitle(4, 'Aggregation')

    testHelp('Aggregations are useful to generate')
    cy.get('#node-update-form').contains('Aggregations')
    cy.get('#node-update-form').contains('Group columns')

    addFormToFormset('columns')
    cy.get('select[name=columns-0-column]').should('have.value', '').select('Location')
    cy.contains('Save & Preview').click()
    cy.contains('count').should('be.visible')
    cy.contains('5').should('be.visible')

    addFormToFormset('aggregations')
    cy.get('select[name=aggregations-0-column]').should('have.value', '').select('Employees')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'count')
    cy.get('#workflows-grid').contains('45')

    cy.get('select[name=aggregations-0-function]').select('MEAN')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', '45')
    cy.get('#workflows-grid').contains('9.0').should('be.visible')

    cy.get('select[name=aggregations-0-column]').select('Owner')
    cy.get('select[name=aggregations-0-function]')
      .should('not.contain', 'MEAN')
      .should('have.value', 'count')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'count')
    cy.get('#workflows-grid').contains('5').should('be.visible')

    // TODO: Test formset deletion
  })

  it('Sort', () => {
    openModalAndCheckTitle(5, 'Sort')
    cy.contains('Sort columns')
    testHelp('Sort the table based')

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
    cy.contains('Loading preview...').should('be.visible')

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
    cy.contains('Offset').should('be.visible')

    cy.contains('Result').click()
    cy.get('#workflows-grid tbody tr').should('have.length', 15)
    cy.get('input[name=limit_limit]').clear().type(5)
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid tbody tr').should('have.length', 5)
    cy.get('#workflows-grid').contains('Floris').should('be.visible')

    cy.get('input[name=limit_offset]').type(3)
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').should('not.contain', 'Floris')
    cy.get('#workflows-grid tbody tr').should('have.length', 5)
  })

  it('Filter', () => {
    openModalAndCheckTitle(7, 'Filter')
    cy.get('#workflows-grid tbody tr').should('have.length', 15)
    testHelp('Filter a table by different conditions')

    cy.get('select[name=filters-0-numeric_predicate]').should('not.exist')
    cy.get('input[name=filters-0-integer_value]').should('not.exist')
    cy.get('select[name=filters-0-column]').should('have.value', '').select('store_id')
    cy.get('select[name=filters-0-numeric_predicate]')
      .should('have.value', '')
      .select('greater than')
    cy.get('input[name=filters-0-integer_value]').should('have.value', '').type('5{enter}')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid tbody tr').should('have.length', 10)

    cy.get('select[name=filters-0-column]').select('Location')
    cy.get('select[name=filters-0-string_predicate]')
      .should('not.contain', 'greater than')
      .select('is equal to')
    cy.get('input[name=filters-0-string_value]').should('have.value', '').type('Edinburgh{enter}')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid tbody tr').should('have.length', 3)
    cy.get('#workflows-grid').should('not.contain', 'Blackpool')

    addFormToFormset('filters')
    cy.get('select[name=filters-1-column]').select('Employees')
    cy.get('select[name=filters-1-numeric_predicate]').select('less than or equal')
    cy.get('input[name=filters-1-integer_value]').should('have.value', '').type('7{enter}')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid tbody tr').should('have.length', 2)
    // TODO: Test filter deletion
  })

  it('Distinct', () => {
    openModalAndCheckTitle(8, 'Distinct')
    cy.get('td:contains(Blackpool)').should('have.length', 4)
    testHelp('Select columns that should')

    cy.contains('Location').click()
    cy.contains('Save & Preview').click()
    cy.get('td:contains(Blackpool)').should('have.length', 1)
  })

  it('Pivot', () => {
    openModalAndCheckTitle(9, 'Pivot')
    testHelp("Turn the pivot column's rows into")

    cy.get('select[name=pivot_index]').select('Owner')
    cy.get('select[name=pivot_column]').select('Location')
    cy.get('select[name=pivot_value]').select('Employees')
    cy.contains('Save & Preview').click()

    // TODO: the pivotting takes longer so we have to wait
    cy.get('th:contains(Blackpool)', { timeout: 10000 }).should('exist')
    cy.get('#workflows-grid td:contains(Matt)').should('have.length', 1)
    cy.get('#workflows-grid td:contains(nan)').should('have.length', 8)
  })

  it('Edit', () => {
    openModalAndCheckTitle(11, 'Edit')
    testHelp('Select columns you would like to edit ')

    cy.get('select[name=edit_columns-0-column]').should('have.value', '').select('Employees')
    cy.get('select[name=edit_columns-0-integer_function]')
      .should('have.value', '')
      .select('square root')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').contains('3.0')

    addFormToFormset('edit_columns')
    cy.get('select[name=edit_columns-1-column]').select('Owner')
    cy.get('select[name=edit_columns-1-string_function]').select('like')
    cy.get('textarea[name=edit_columns-1-string_value]').type('Matt').blur()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid tbody td:contains(True)').should('have.length', 6)
  })

  it('Add', () => {
    openModalAndCheckTitle(12, 'Add')
    testHelp('Add new columna by selecting')

    cy.get('select[name=add_columns-0-column]').should('have.value', '').select('store_id')
    cy.get('select[name=add_columns-0-integer_function').should('have.value', '').select('divide')
    cy.get('input[name=add_columns-0-float_value]').should('have.value', '').type('10{enter}')
    cy.get('input[name=add_columns-0-label]')
      .should('have.value', '')
      .should('not.be.disabled')
      .type('magic_number')
      .blur()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').contains('magic_number').should('be.visible')
    cy.get('#workflows-grid').contains('0.1').should('be.visible')

    addFormToFormset('add_columns')
    cy.get('select[name=add_columns-1-column]').select('Owner')
    cy.get('select[name=add_columns-1-string_function').select('to uppercase')
    cy.get('select[name=add_columns-1-string_value]').should('not.exist')
    cy.get('input[name=add_columns-1-label]').type('upper_owner{enter}')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid:contains(upper_owner)').scrollIntoView()
    cy.get('#workflows-grid').contains('ALEX').should('be.visible')
  })

  it('Rename', () => {
    openModalAndCheckTitle(13, 'Rename')
    cy.get('#workflows-grid').contains('store_id').should('be.visible')
    testHelp('Select the columns you want to rename')

    cy.get('select[name=rename_columns-0-column]').select('store_id')
    cy.get('input[name=rename_columns-0-new_name]').clear().type('unique_id').blur()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').contains('unique_id').should('be.visible')

    addFormToFormset('rename_columns')
    cy.get('select[name=rename_columns-1-column]').select('Location')
    cy.get('input[name=rename_columns-1-new_name]').clear().type('city').blur()
    cy.contains('Save & Preview').click()
    cy.contains('Loading preview...')
    cy.get('#workflows-grid').contains('city').should('be.visible')
  })

  // TODO: Test formula docs separately

  it('Formula', () => {
    // Tests autocomplete for columns and functions
    // and whether arithmetic and functions return right results
    // for + and join
    openModalAndCheckTitle(14, 'Formula')
    testHelp('Formula Docs')

    // We can't type into the codemirror divs but we can use the hidden textarea
    cy.get('#node-update-form .CodeMirror textarea').type('store', { force: true })
    // Check for autocomplete
    cy.get('.CodeMirror-hints').contains('store_id').should('be.visible')
    cy.get('#node-update-form .CodeMirror textarea').type('{enter} + 200', { force: true })
    cy.get('input[name=formula_columns-0-label]').type('glorious_id').blur()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').contains('201').should('be.visible')

    addFormToFormset('formula_columns')
    cy.get('#node-update-form .CodeMirror textarea').eq(1).type('j', { force: true })
    cy.get('.CodeMirror-hints').contains('join').should('be.visible')
    cy.get('#node-update-form .CodeMirror textarea')
      .eq(1)
      .type('{enter}("",Loc{enter},Ow{enter})', { force: true })
    cy.get('input[name=formula_columns-1-label]').type('loco').blur()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid:contains(loco)').scrollIntoView().should('be.visible')
    cy.get('#workflows-grid').contains('BlackpoolKanar').should('be.visible')
  })

  it('Window', () => {
    openModalAndCheckTitle(15, 'Window')
    testHelp('Window functions aggregate over the selected')
    cy.contains('Window columns').should('be.visible')

    // TODO: test whether saving with optional input work
    cy.get('select[name=window_columns-0-column]').select('Employees')
    cy.get('select[name=window_columns-0-group_by]').select('Location')
    cy.get('select[name=window_columns-0-order_by]').select('store_id')
    cy.get('input[name=window_columns-0-label').type('sum_emp').blur()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid th:contains(sum_emp)').should('be.visible')
  })

  it('Text', () => {
    // Test whether text is persisted
    cy.visit('/projects/2/workflows/1')

    const text = 'Here is some example text'
    cy.get('[data-id=16] textarea')
      .invoke('attr', 'placeholder')
      .should('equal', 'Leave a note to annotate the workflow...')
    cy.get('[data-id=16] textarea').type(text).blur()

    // Need to wait for the sync to have been committed before reloading
    cy.wait(200)
    cy.visit('/projects/2/workflows/1')
    cy.get('[data-id=16] textarea').should('have.value', text)
  })

  it('Join', () => {
    openModalAndCheckTitle(18, 'Join')
    testHelp('Merge two tables side by side meaning ')

    // TODO: maybe show none selected instead
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid').contains('store_id_1').should('be.visible')
    cy.get('#workflows-grid').contains('revenue').should('be.visible')
  })

  it('Union', () => {
    openModalAndCheckTitle(21, 'Union')
    testHelp('Concatenates two or more tables by adding')

    cy.contains('Result').click()
    cy.get('#node-update-form').contains('mode').should('be.visible')
    cy.get('#node-update-form').contains('distinct').should('be.visible')
    // TODO: check for visibility once visual bug is fixed
    cy.get('#workflows-grid').contains('next')

    cy.get('select[name=union_mode]').select('exclude')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid:contains(Blackpool)').should('not.exist')

    cy.get('select[name=union_mode]').select('keep')
    cy.get('input[name=union_distinct]').check()
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid td:contains(Edinburgh)').should('have.length', 3)
    cy.get('#workflows-grid:contains(next)').should('not.exist')
  })

  it('Intersect', () => {
    openModalAndCheckTitle(22, 'Intersection')
    cy.get('#workflows-grid td:contains(London)').should('not.exist')
    testHelp('Calculate the overlapping rows')
  })

  it('Unpivot', () => {
    openModalAndCheckTitle(24, 'Unpivot')
    testHelp('Turn columns into row values and spread the values')

    cy.get('input[name=unpivot_value]').type('sales').blur()
    waitForLiveFormUpdate()
    cy.get('input[name=unpivot_column]').should('not.be.disabled').type('quarter').blur()
    waitForLiveFormUpdate()
    cy.get('select[name=columns-0-column').select('Q1')
    waitForLiveFormUpdate()
    addFormToFormset('columns')
    cy.get('select[name=columns-1-column').select('Q2')
    waitForLiveFormUpdate()
    addFormToFormset('columns')
    cy.get('select[name=columns-2-column').select('Q3')
    waitForLiveFormUpdate()
    addFormToFormset('columns')
    cy.get('select[name=columns-3-column').select('Q4')
    cy.contains('Save & Preview').click()

    cy.get('#workflows-grid th:contains(quarter)', { timeout: 10000 }).should('be.visible')
    cy.get('#workflows-grid th:contains(sales)').should('be.visible')
    cy.get('#workflows-grid td:contains(Q1)').should('have.length', 2)
    cy.get('#workflows-grid th:contains(product)').should('not.exist')

    addFormToFormset('secondary_columns')
    cy.get('select[name=secondary_columns-0-column]').select('product')
    cy.contains('Save & Preview').click()
    cy.get('#workflows-grid th:contains(product)', { timeout: 10000 }).should('be.visible')
    cy.get('#workflows-grid td:contains(Kale)').should('have.length', 4)
  })

  it('Tests unconnected modal screen', () => {
    cy.visit(`/projects/2/workflows/1`)
    cy.get('[data-id=25] [title="Aggregation node needs to be connected to a node"]')
    cy.get('[data-id=25]').dblclick()
    cy.contains(
      'This node needs to be connected to more than one node before you can configure it.'
    )
  })
})
