import { Controller } from '@hotwired/stimulus';

export default class extends Controller {
  connect() {
    // Could be replaced by requestAnimationFrame()
    setTimeout(() => {
      [...this.element.children].map((el) => this.activateScript(el));
    }, 300);
  }

  removeScript(element) {
    if (element.nodeName == "SCRIPT") {
      element.parentElement?.removeChild(element);
    }
  }

  activateScript(element) {
    if (element.nodeName == "SCRIPT") {
      const createdScriptElement = document.createElement("script");
      createdScriptElement.textContent = element.textContent;
      createdScriptElement.async = false;
      this.copyElementAttributes(createdScriptElement, element);
      this.replaceElementWithElement(element, createdScriptElement);
    }
  }

  replaceElementWithElement(fromElement, toElement) {
    const parentElement = fromElement.parentElement;
    if (parentElement) {
      return parentElement.replaceChild(toElement, fromElement);
    }
  }

  copyElementAttributes(destinationElement, sourceElement) {
    for (const { name, value } of [...sourceElement.attributes]) {
      destinationElement.setAttribute(name, value);
    }
  }
}