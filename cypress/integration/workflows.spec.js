/// <reference types="cypress" />
import { getModelStartId } from '../support/utils'

const startId = getModelStartId('nodes.node')

describe('workflows', () => {
  beforeEach(() => {
    cy.login()
    cy.visit('/projects/1/workflows/')
    cy.contains('You have no workflows')
  })

  it('create, rename, duplicate and delete workflow', () => {
    cy.story('Create and rename workflow')
    cy.get('button[type=submit]').first().click()
    cy.contains('Loading...')
    cy.get('input[id=name]').clear().type('Magical workflow{enter}')
    cy.contains('Start building your workflow by dragging in a Get data node')
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

    const inputId = `[data-id=${startId}]`
    cy.get(inputId).dblclick()
    cy.contains('store_info').click()
    cy.contains('Save & Preview').click()
    cy.contains('Blackpool')
    cy.get('button[class=tf-modal__close]').click()
    cy.reactFlowDrag(inputId, { x: 150, y: 300 })

    cy.story('Drop, connect and configure select node')
    cy.drag('[id=dnd-node-select]')
    cy.drop('[class=react-flow]')

    const selectId = `[data-id=${startId + 1}]`
    cy.get(selectId).should('exist')
    cy.connectNodes(inputId, selectId)
    cy.get('.react-flow__edge').should('have.length', 1)
    cy.get(selectId).dblclick()
    cy.get('.workflow-detail__sidebar').within(() => {
      cy.contains('Location').click()
      cy.contains('Employees').click()
      cy.contains('Owner').click()
    })
    cy.contains('Save & Close').click()
    cy.reactFlowDrag(selectId, { x: 300, y: 100 })
    cy.story('Drop, connect and name output node')
    cy.drag('[id=dnd-node-output]')
    cy.drop('[class=react-flow]')

    const outputId = `[data-id=${startId + 2}]`
    cy.get(outputId).should('exist')
    cy.connectNodes(selectId, outputId)
    cy.get('.react-flow__edge').should('have.length', 2)
    cy.get(outputId).dblclick()
    cy.get('[name=output_name').type('Goblet of fire')
    cy.contains('Save & Close').click()

    cy.story('Run workflow')
    cy.contains('Run').click()
    cy.contains('Last run')
    cy.get('.sidebar__link--active').click()
    cy.contains('Uptodate')
  })

  it('Shows schemajs failed loading screen', () => {
    cy.window().then((win) => {
      delete win.schema
    })
    cy.get('button[type=submit]').first().click()
    cy.contains('Loading')
    cy.contains('Something went wrong!', { timeout: 8000 })
  })

  it.only('Shows nodes loading error', () => {
    cy.intercept('GET', `/nodes/api/nodes/?workflow=${getModelStartId('workflows.workflow')}`, {
      statusCode: 500,
    })
    cy.get('button[type=submit]').first().click()
    cy.contains('Loading...')
    cy.contains('Failed loading your nodes!')
  })
})
