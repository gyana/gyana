import { Controller } from 'stimulus'

/**
 * Controls the zindex of entities contained by the element this controller is bound to.
 *
 * Avoids overlap in freeform environments.
 */
export default class extends Controller {
  static targets = ['entity']

  register(event) {
    const entities = this.entityTargets

    entities.forEach((target) => {
      target.onmousedown = function () {
        entities.forEach((entity) => {
          entity.style.zIndex = null
        })
        target.style.zIndex = 1
      }
    })

    // When event is defined it means this function is called from a DOM element
    // which then means that we need to register a new entity. To make sure
    // we keep the overlap consistent for this new element we manually set
    // the zindex for the closest entity target
    if (event) {
      const closest = event.target.closest('[data-zindex-target="entity"]')
      entities.forEach((entity) => {
        entity.style.zIndex = null
      })
      closest.style.zIndex = 1
    }
  }

  connect() {
    this.register()
  }
}
