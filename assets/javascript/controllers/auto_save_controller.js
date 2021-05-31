import { Controller } from "stimulus";

export default class extends Controller {
  listener = () => {
    // requestSubmit required for turbo-frame
    this.element.requestSubmit();
  };

  connect() {
    this.element.addEventListener("change", this.listener);
  }
}
