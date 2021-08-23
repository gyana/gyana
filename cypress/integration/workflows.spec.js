/// <reference types="cypress" />
import { getModelStartId } from '../support/utils'
const { _ } = Cypress

const startId = getModelStartId('nodes.node')
const getNodePositions = (nodes$) =>
  _.map(nodes$, (el$) => {
    const transform = el$.style.transform
      .replace('translate(', '')
      .replace(')', '')
      .replace('px', '')
      .replace('px', '')
    const [x, y] = transform.split(', ').map((n) => Number(n))
    const id = Number(el$.getAttribute('data-id'))
    return { x, y, id }
  })

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

    cy.get(`[data-id=${startId}]`).dblclick()
    cy.contains('store_info').click()
    cy.contains('Save & Preview').click()
    cy.contains('Blackpool')
    cy.get('button[class=tf-modal__close]').click()
    cy.reactFlowDrag(startId, { x: 150, y: 300 })

    cy.story('Drop, connect and configure select node')
    cy.drag('[id=dnd-node-select]')
    cy.drop('[class=react-flow]')

    const selectId = startId + 1
    cy.get(`[data-id=${selectId}]`).should('exist')
    cy.connectNodes(startId, selectId)
    cy.get('.react-flow__edge').should('have.length', 1)
    cy.get(`[data-id=${selectId}]`).dblclick()
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

    const outputId = startId + 2
    cy.get(`[data-id=${outputId}]`).should('exist')
    cy.connectNodes(selectId, outputId)
    cy.get('.react-flow__edge').should('have.length', 2)
    cy.get(`[data-id=${outputId}]`).dblclick()
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

  it('Shows nodes loading error', () => {
    cy.intercept('GET', `/nodes/api/nodes/?workflow=${getModelStartId('workflows.workflow')}`, {
      statusCode: 500,
    })
    cy.get('button[type=submit]').first().click()
    cy.contains('Loading...')
    cy.contains('Failed loading your nodes!')
  })
})

describe('Workflow-format', () => {
  it('Formats a workflow', () => {
    cy.login()
    cy.visit('/projects/2/workflows/1')

    const movedNodes = [6, 8, 11, 13]
    cy.reactFlowDrag(6, { x: 100, y: 400 })
    cy.reactFlowDrag(8, { x: 200, y: 300 })
    cy.reactFlowDrag(11, { x: 300, y: 200 })
    cy.reactFlowDrag(13, { x: 500, y: 100 })

    cy.get('.react-flow__node')
      .then(getNodePositions)
      .then((nodes) => {
        const filtered = nodes.filter((n) => movedNodes.includes(n.id))
        const xSorted = _.sortBy(filtered, (n) => n.x).map((n) => n.id)
        expect(xSorted).to.deep.equal(movedNodes)

        const ySorted = _.reverse(_.sortBy(filtered, (n) => n.y)).map((n) => n.id)
        expect(ySorted).to.deep.equal(movedNodes)
      })
    cy.get('.react-flow__controls-button').eq(4).click()
    cy.get('.react-flow__node')
      .then(getNodePositions)
      .then((nodes) => {
        const filtered = nodes.filter((n) => movedNodes.includes(n.id))

        const xValue = Math.round(filtered[0].x)
        filtered.forEach((n) => {
          expect(Math.round(n.x)).to.equal(xValue)
        })

        const ySorted = _.sortBy(filtered, (n) => n.y).map((n) => n.id)
        expect(ySorted).to.deep.equal(movedNodes)
      })
  })
})
