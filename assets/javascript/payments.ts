'use strict';

import Cookies from 'js-cookie';

export function addInputToForm(form, name, value) {
  const hiddenInput = document.createElement('input');
  hiddenInput.setAttribute('type', 'hidden');
  hiddenInput.setAttribute('name', name);
  hiddenInput.setAttribute('value', value);
  form.appendChild(hiddenInput);
}

export function showOrClearError(errorMessage) {
  const displayError = document.getElementById('card-errors');
  if (errorMessage) {
    displayError.textContent = errorMessage;
  } else {
    displayError.textContent = '';
  }
}

export function createCardElement(stripe) {
  let elements = stripe.elements();
  const classes = {
    base: 'stripe-element',
    focus: 'focused-stripe-element',
    invalid: 'invalid-stripe-element',
    complete: 'complete-stripe-element',
  };
  const style = {
      base: {
        fontSize: '16px',
      }
  };
  // Create an instance of the card Element.
  let cardElement = elements.create('card', {classes: classes, style: style});
  cardElement.mount("#card-element");
  cardElement.addEventListener('change', function (event) {
    const errorMessage = event.error ? event.error.message : '';
    showOrClearError(errorMessage);
  });
  return cardElement;
}

export const createPaymentIntent = function(createPaymentIntentUrl, paymentData) {
  // creates a payment intent in stripe and populates the result in the passed in clientSecrets dictionary
  // (potentially overwriting what was previous there, in the case of a coupon changing the price)
  // returns a promise
  return new Promise((resolve, reject) => {
    const csrfToken = Cookies.get('csrftoken');
    paymentData = paymentData || {};
    fetch(createPaymentIntentUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'X-CSRFToken': csrfToken,
      },
      credentials: 'same-origin',
      body: JSON.stringify(paymentData),
    }).then((result) => {
      return result.json();
    })
    .then((data) => {
      resolve(data.client_secret);
    }).catch((error) => {
      reject(error);
    });
  });
};


export const Payments = {
  addInputToForm: addInputToForm,
  createCardElement: createCardElement,
  createPaymentIntent: createPaymentIntent,
  showOrClearError: showOrClearError,
};
