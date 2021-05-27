import { Controller } from "stimulus";

// Trigger an event on click

export default class extends Controller {
  static values = {
    event: String,
  };
  static targets = ["turboFrame"];

  refresh() {
    const src = this.turboFrameTarget.src;
    this.turboFrameTarget.removeAttribute("src");
    this.turboFrameTarget.innerHTML = "Loading ...";
    this.turboFrameTarget.setAttribute("src", src);
  }

  connect(){
    const refresh = this.refresh.bind(this)
    window.addEventListener(this.eventValue, refresh)
  }

  disconnect() {
    window.removeEventListener(this.eventValue, this.refresh)
  }
}