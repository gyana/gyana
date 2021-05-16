import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ["modal"];

  open() {
    this.modalTarget.classList.remove("hidden");
  }
}
