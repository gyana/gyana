import { Controller } from "stimulus";

// Refresh turbo-frame by action

export default class extends Controller {
  static targets = ["turboFrame"];

  refresh() {
    const src = this.turboFrameTarget.src;
    this.turboFrameTarget.removeAttribute("src");
    this.turboFrameTarget.innerHTML = "Loading ...";
    this.turboFrameTarget.setAttribute("src", src);
  }
}
