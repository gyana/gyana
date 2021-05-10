"use strict";
import React from "react";
import ReactDOM from "react-dom";
import DnDFlow from "./dnd-flow";

let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: "csrftoken",
  csrfHeaderName: "X-CSRFToken",
});

let client = new coreapi.Client({ auth: auth });
let domContainer = document.querySelector("#react-app");
domContainer
  ? ReactDOM.render(<DnDFlow client={client} />, domContainer)
  : null;
