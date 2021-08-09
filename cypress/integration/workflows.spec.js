/// <reference types="cypress" />

describe('workflows', () => {
  beforeEach(() => {
    cy.login()
    cy.visit('/projects/1/workflows/')
    cy.contains('You have no workflows')
  })

  it('create, rename, duplicate and delete workflow', () => {
    cy.story('Create and rename workflow')
    cy.get('button[type=submit]').first().click()
    cy.get('input[id=name]').clear().type('Magical workflow{enter}')
    cy.visit('/projects/1/workflows/')
    cy.get('table').contains('Magical workflow')

    cy.story('Duplicate workflow and delete duplicate ')
    cy.get('table').within(() => cy.get('button[type=submit]').click())
    cy.contains('Copy of Magical workflow').click()
    cy.get('span[data-popover-target=trigger]').click()
    cy.contains('Yes').click()
    cy.contains('Copy of Magical workflow').should('not.exist')
  })

  it('runnable workflow', () => {
    cy.get('button[type=submit]').first().click()
    cy.contains('Press the run button after adding some nodes to run this workflow')

    cy.story('Drop and configure an input node')
    cy.drag('[id=dnd-node-input]')
    cy.drop('.react-flow')
    cy.get('[data-id=1]').dblclick()
    cy.contains('store_info').click()
    cy.contains('Save & Preview').click()
    cy.contains('Blackpool')
    cy.get('button[class=tf-modal__close]').click()
    cy.reactFlowDrag('[data-id=1]', { x: 150, y: 300 })

    cy.story('Drop, connect and configure select node')
    cy.drag('[id=dnd-node-select]')
    cy.drop('[class=react-flow]')
    cy.get('[data-id=2]').should('exist')
    cy.connectNodes('[data-id=1]', '[data-id=2]')
    cy.get('.react-flow__edge').should('have.length', 1)
    cy.get('[data-id=2]').dblclick()
    cy.get('.workflow-detail__sidebar').within(() => {
      cy.contains('Location').click()
      cy.contains('Employees').click()
      cy.contains('Owner').click()
    })
    cy.contains('Save & Close').click()
    cy.reactFlowDrag('[data-id=2]', { x: 300, y: 100 })
    cy.story('Drop, connect and name output node')
    cy.drag('[id=dnd-node-output]')
    cy.drop('[class=react-flow]')
    cy.get('[data-id=3]').should('exist')
    cy.connectNodes('[data-id=2]', '[data-id=3]')
    cy.get('.react-flow__edge').should('have.length', 2)
    cy.get('[data-id=3]').dblclick()
    cy.get('[name=output_name').type('Goblet of fire')
    cy.contains('Save & Close').click()

    cy.story('Run workflow')
    cy.contains('Run').click()
    cy.contains('Last run')
    cy.get('.sidebar__link--active').click()
    cy.contains('Uptodate')
  })
})
