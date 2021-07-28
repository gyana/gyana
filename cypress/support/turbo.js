// Utilities to get Cypress and Turbo to work together

const isTurbo = (el) => {
  // using el.closest to check all parent elemnts
  const isLink = el.closest('a')?.getAttribute('href')
  const isSubmit = el.closest('input[type=submit],button[type=submit]')
  const dataTurboFalse = el.closest('[data-turbo=false]')

  return (isLink || isSubmit) && !dataTurboFalse
}

const isWithinTurboFrame = (el) => el.closest('turbo-frame:not(turbo-frame[data-turbo=false])')

// Adapted from https://github.com/cypress-io/cypress/issues/1938#issuecomment-502201139
// Wait for turbo:load event before running original function
const click = (originalFn, subject, ...args) => {
  const lastArg = args.length ? args[args.length - 1] : {}
  const el = subject[0]
  // check if turbo could be active for this click event
  if ((typeof lastArg !== 'object' || !lastArg['noWaiting']) && isTurbo(el)) {
    cy.document({ log: false }).then(($document) => {
      Cypress.log({
        $el: subject,
        name: 'click',
        displayName: 'click',
        message: 'click and wait for page to load',
        consoleProps: () => ({ subject: subject }),
      })
      const event = isWithinTurboFrame(el) ? 'turbo:before-fetch-response' : 'turbo:load'

      return new Cypress.Promise((resolve) => {
        const onTurboLoad = () => {
          $document.removeEventListener(event, onTurboLoad)
          resolve()
        }
        $document.addEventListener(event, onTurboLoad)
        originalFn(subject, ...args)
      })
    })
  } else {
    return originalFn(subject, ...args)
  }
}

Cypress.Commands.overwrite('click', click)
