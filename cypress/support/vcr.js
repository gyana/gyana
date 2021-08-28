function string_to_slug(str) {
  str = str.replace(/^\s+|\s+$/g, '') // trim
  str = str.toLowerCase()

  // remove accents, swap ñ for n, etc
  var from = 'àáäâèéëêìíïîòóöôùúüûñç·/_,:;'
  var to = 'aaaaeeeeiiiioooouuuunc------'
  for (var i = 0, l = from.length; i < l; i++) {
    str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i))
  }

  str = str
    .replace(/[^a-z0-9 -]/g, '') // remove invalid chars
    .replace(/\s+/g, '-') // collapse whitespace and replace by -
    .replace(/-+/g, '-') // collapse dashes

  return str
}

const startVCR = (suite, test) => {
  const name = string_to_slug(test)
  cy.request(`/cypress/vcr/start/${suite}/${name}`).then((resp) => {
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
