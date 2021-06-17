import { Controller } from "stimulus"

export default class extends Controller {
  static targets = ["body"]

  toggle() {
    this.element.classList.toggle("active");

    if (this.bodyTarget.style.maxHeight) {
      this.bodyTarget.style.maxHeight = null;
    } else {
      this.bodyTarget.style.maxHeight = this.bodyTarget.scrollHeight + "px";
    }
  }
}