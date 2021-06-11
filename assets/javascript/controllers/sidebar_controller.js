import { Controller } from "stimulus"

export default class extends Controller {
  static targets = ["toggle"]

  initialize() {
    this.sidebar_collapsed = localStorage.getItem("sidebar_collapsed") === "true"

    this.toggleTarget.checked = this.sidebar_collapsed
  }

  toggle() {
    localStorage.setItem("sidebar_collapsed", !this.sidebar_collapsed)
    this.sidebar_collapsed = !this.sidebar_collapsed
  }
}