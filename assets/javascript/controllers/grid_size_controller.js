import { Controller } from 'stimulus'

// The grid layout (on any screen) has 80 columns
// Make sure this is the same as in GyWidget
const GRID_COLS = 80

export default class extends Controller {
  connect() {
    const width = this.element.offsetWidth
    const gridSize = Math.floor(width / GRID_COLS)
    this.element.style.setProperty('--grid-size', `${gridSize}px`)
  }
}
