import { Controller } from "stimulus";
import Sortable from "sortablejs";

// Sortable elements
// Inspired by https://github.com/stimulus-components/stimulus-sortable/blob/master/src/index.js

export default class extends Controller {
  static values = {
    id: String,
  };

  connect() {
    const auth = new coreapi.auth.SessionAuthentication({
      csrfCookieName: "csrftoken",
      csrfHeaderName: "X-CSRFToken",
    });

    this.client = new coreapi.Client({ auth: auth });

    this.sortable = Sortable.create(this.element, {
      handle: ".sortable-handle",
      onUpdate: (event) => {
        this.client.action(
          window.schema,
          ["dashboards", "sort", "partial_update"],
          {
            id: this.idValue,
            sort_order: this.sortable.toArray().map((x) => parseInt(x)),
          }
        );
      },
    });
  }

  disconnect() {
    this.sortable.destroy();
    this.sortable = undefined;
  }
}
