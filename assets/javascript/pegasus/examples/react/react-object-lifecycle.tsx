'use strict';
import React from "react";
import ReactDOM from "react-dom";
import EmployeeApplication from "./App";


let auth = new coreapi.auth.SessionAuthentication({
  csrfCookieName: 'csrftoken',
  csrfHeaderName: 'X-CSRFToken'
});
let client = new coreapi.Client({auth: auth});
let domContainer = document.querySelector('#object-lifecycle-home');
domContainer ? ReactDOM.render(
  <EmployeeApplication client={client}/>
  , domContainer) : null;
