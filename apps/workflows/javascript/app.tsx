"use strict";
import React from "react";
import ReactDOM from "react-dom";
import { ReactFlowProvider } from "react-flow-renderer";
import DnDFlow from "./dnd-flow";

let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: "csrftoken",
  csrfHeaderName: "X-CSRFToken",
});

let client = new coreapi.Client({ auth: auth });
let domContainer = document.querySelector("#react-app");
domContainer
  ? ReactDOM.render(
      <ReactFlowProvider>
        <DnDFlow client={client} />
      </ReactFlowProvider>,
      domContainer
    )
  : null;
