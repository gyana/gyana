// Utilities to get Cypress and Turbo to work together

// Turbo overrides link clicks, fetches the HTML in the background and updates
// the DOM. Unfortunately, Cypress is not aware of this and by default does not
// not wait for the operation to complete.

// Example bug: Cypress clicks a link, and proceeds to the next instruction to
// select an item on the page. Turbo then overwrites the page, and the DOM element
// Cypress referred to is no longer valid, breaking subsequent commands.

// This solution uses events emitted by Turbo to wait until the operation is completed
// Adapted from https://github.com/cypress-io/cypress/issues/1938#issuecomment-502201139

const isTurbo = (el) => {
  // check if turbo could be active for this click event
  // using el.closest to check all parent elements
  const isLink = el.closest('a')?.getAttribute('href')
  const isSubmit = el.closest('input[type=submit],button[type=submit]')
  const dataTurboFalse = el.closest('[data-turbo=false]')

  return (isLink || isSubmit) && !dataTurboFalse
}

// check if it is enclosed in an active turbo-frame
const isWithinTurboFrame = (el) => el.closest('turbo-frame:not(turbo-frame[data-turbo=false])')

// Wait for turbo:load event before running original function
const click = (originalFn, subject, ...args) => {
  const lastArg = args.length ? args[args.length - 1] : {}
  const el = subject[0]
  if ((typeof lastArg !== 'object' || !lastArg['noWaiting']) && isTurbo(el)) {
    cy.document({ log: false }).then(($document) => {
      Cypress.log({
        $el: subject,
        name: 'click',
        displayName: 'click',
        message: 'click and wait for page to load',
        consoleProps: () => ({ subject: subject }),
      })
      // Turbo Drive: turbo:load event is emitted when completed
      // Turbo Frame: there is no explicit event, the closest is turbo:before-fetch-response
      //    TODO: Possibly better solution is to wait for `FrameElement.loaded` promise to resolve
      // Turbo Stream: NYI
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
