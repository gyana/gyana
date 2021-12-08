/// <reference types="cypress" />

describe('Api access control', () => {
  it('Node ViewSet', () => {
    cy.login()
    cy.request('/nodes/api/nodes').then((response) => {
      expect(response.status).to.equal(200)
      const data = response.body.results
      expect(data).to.have.length(32)
      expect(data.map((node) => node.id)).to.contain(1)
    })

    cy.logout()

    cy.request({ url: '/nodes/api/nodes', failOnStatusCode: false }).then((response) => {
      expect(response.status).to.equal(403)
    })

    cy.login('alone@gyana.com')
    cy.request('/nodes/api/nodes').then((response) => {
      expect(response.status).to.equal(200)
      const data = response.body.results

      expect(data).to.have.length(0)
      expect(data.map((node) => node.id)).to.not.contain(1)
    })
  })
})
