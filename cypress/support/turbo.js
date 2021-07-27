// Utilities to get Cypress and Turbo to work together

const isLink = (el) => el.tagName === 'A' && el.getAttribute('href')
const isFormSubmit = (el) =>
  ['INPUT', 'BUTTON'].includes(el.tagName) && el.getAttribute('type') === 'submit'
const turboEnabled = (el) => !el.closest('[data-turbo=false]') // check all parent elements

// Adapted from https://github.com/cypress-io/cypress/issues/1938#issuecomment-502201139
// Wait for turbo:load event before running original function
const click = (originalFn, subject, ...args) => {
  var lastArg = args.length ? args[args.length - 1] : {}
  const el = subject[0]
  // check if turbo could be active for this click event
  if (
    (typeof lastArg !== 'object' || !lastArg['noWaiting']) &&
    (isLink(el) || isFormSubmit(el)) &&
    turboEnabled(el)
  ) {
    cy.document({ log: false }).then(($document) => {
      Cypress.log({
        $el: subject,
        name: 'click',
        displayName: 'click',
        message: 'click and wait for page to load',
        consoleProps: () => ({ subject: subject }),
      })
      return new Cypress.Promise((resolve) => {
        const onTurboLoad = () => {
          $document.removeEventListener('turbo:load', onTurboLoad)
          resolve()
        }
        $document.addEventListener('turbo:load', onTurboLoad)
        originalFn(subject, ...args)
      })
    })
  } else {
    return originalFn(subject, ...args)
  }
}

Cypress.Commands.overwrite('click', click)
