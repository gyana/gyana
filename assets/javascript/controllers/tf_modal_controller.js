import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ["modal", "turboFrame"];

  open(event) {
    this.modalTarget.classList.remove("hidden");
    this.turboFrameTarget.setAttribute(
      "src",
      event.target.getAttribute("data-src")
    );
  }

  close() {
    this.modalTarget.classList.add("hidden");
  }
}
