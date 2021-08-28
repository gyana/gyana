const startVCR = () => {
  const name = Cypress.mocha.getRunner().suite.ctx.test
  cy.request(`/cypress/vcr/start/${name}`).then((resp) => {
    expect(resp.status).to.eq(200)
  })
}

Cypress.Commands.add('startVCR', startVCR)

const stopVCR = () => {
  cy.request(`/cypress/vcr/stop`).then((resp) => {
    expect(resp.status).to.eq(200)
  })
}

Cypress.Commands.add('stopVCR', stopVCR)
