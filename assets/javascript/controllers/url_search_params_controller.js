import { Controller } from "stimulus";

export default class extends Controller {
  static values = {
    key: String,
    val: String,
  };

  add() {
    const params = new URLSearchParams(location.search);
    params.set(this.keyValue, this.valValue);
    history.replaceState({}, "", `${location.pathname}?${params.toString()}`);
  }

  remove() {
    const params = new URLSearchParams(location.search);
    params.remove(this.keyValue);
    history.replaceState({}, "", `${location.pathname}?${params.toString()}`);
  }
}
