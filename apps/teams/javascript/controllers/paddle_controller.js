import { Controller } from '@hotwired/stimulus'

import getSymbolFromCurrency from 'currency-symbol-map'

export default class extends Controller {
  static values = {
    vendorId: Number,
    sandbox: Boolean,
    debug: Boolean,
    plan: String,
    email: String,
    marketingConsent: Number,
    passthrough: String,
  }

  static targets = ['total', 'recurring', 'checkoutMessage', 'successMessage']

  updatePrices(data) {
    const total = data.eventData.checkout.prices.customer.total
    const currencySymbol = getSymbolFromCurrency(data.eventData.checkout.prices.customer.currency)

    this.totalTarget.innerHTML = `${currencySymbol}${total}`

    const recurringTotal = data.eventData.checkout.recurring_prices.customer.total
    const recurringCurrencySymbol = getSymbolFromCurrency(
      data.eventData.checkout.recurring_prices.customer.currency
    )

    this.recurringTarget.innerHTML = `${recurringCurrencySymbol}${recurringTotal}`
  }

  connect() {
    if (this.sandboxValue) {
      Paddle.Environment.set('sandbox')
    }

    Paddle.Setup({
      vendor: this.vendorIdValue,
      debug: this.debugValue,
      eventCallback: (data) => {
        this.updatePrices(data)

        if (data.event === 'Checkout.Complete') {
          // bug fix: by default, dj-paddle will redirect to "null"
          data.eventData.checkout.redirect_url = ''
          window.checkoutComplete(data.eventData)

          this.checkoutMessageTarget.setAttribute('hidden', '')
          this.successMessageTarget.removeAttribute('hidden')
        }
      },
    })

    Paddle.Checkout.open({
      method: 'inline',
      product: this.planValue,
      email: this.emailValue,
      marketingConsent: this.marketingConsentValue,
      passthrough: this.passthroughValue,
      disableLogout: true,
      frameTarget: 'checkout-container',
      frameInitialHeight: 416,
      frameStyle: 'width:100%; min-width:286px; background-color: transparent; border: none;',
    })
  }
}
