import { Controller } from "stimulus";

// Open a modal with the content populated by a turbo-frame

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
