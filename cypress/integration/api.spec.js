/// <reference types="cypress" />

describe('Api access control', () => {
  it('Node ViewSet', () => {
    cy.login()
    cy.request('/nodes/api/nodes').then((response) => {
      expect(response.status).to.equal(200)
      const data = response.body.results
      expect(data).to.have.length(25)
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

  it('Filter autocompletes', () => {
    cy.login()
    cy.request('get', '/filters/autocomplete?q=&parentType=node&parentId=20&column=Employees').then(
      (response) => {
        expect(response.status).to.equal(200)

        const data = response.body
        expect(data).to.have.length(8)
        expect(data).to.contain(12)
      }
    )

    cy.logout()
    cy.login('alone@gyana.com')
    cy.request({
      url: '/filters/autocomplete?q=&parentType=node&parentId=20&column=Employees',
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.equal(404)
    })
  })
})
