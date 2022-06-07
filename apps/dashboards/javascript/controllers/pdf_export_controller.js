import { Controller } from '@hotwired/stimulus'
import html2pdf from "html2pdf.js"

/**
 * Exports a dashboard as a PDF file using html2pdf.
 */
export default class extends Controller {
  initialize() {
    this.boundHandleClick = this.handleClick.bind(this)
  }

  connect() {
    this.element.addEventListener("click", this.boundHandleClick)
  }

  disconnect() {
    this.element.removeEventListener("click", this.boundHandleClick)
  }

  async handleClick() {
    let placeholder = this.createPlaceholder()

    this.element.dataset.disabled = true
    this.element.style.color = "transparent"
    placeholder = this.element.appendChild(placeholder)

    const html2pdfWorker = html2pdf()
    
    await html2pdfWorker
      .from(document.body)
      .set({
        enableLinks: false,
      })
      // Prepare the "fake" container copy so we can adjust it.
      .toContainer()
      
    // This is the container created by html2pdf when we use .toContainer()
    const html2pdfOverlay = document.querySelector('.html2pdf__overlay');
    const container = html2pdfOverlay.querySelector('[id*=dashboard-widget-container]')
    const containerWidth = parseInt(container.dataset.width)
    const containerHeight = parseInt(container.dataset.height)

    html2pdfWorker
      .set({
        jsPDF: {
          format: [containerWidth + 2 + 16 + 16, containerHeight + 2 + 16 + 16 + 16 + 68],
          unit: "px",
          // PDFs are weird and will swap your widths and heights around if you don't
          // explicitly tell it one should be longer than the other.
          orientation: containerWidth > containerHeight ? 'l' : 'p',
          hotfixes: ["px_scaling"],
        },
      })
      .set({
        /**
         * There's quite a lot of magic numbering to explain here.
         * 
         * We parse the set dashboard width as an int so that the pdf
         * output is consistent.
         * 
         * windowWidth and windowHeight are set to consistent values, they
         * can potentially be increased at some point for increased quality.
         */
        html2canvas: {
          backgroundColor: '#fafafc',
          width: containerWidth + 2 + 16 + 16,
          height: (containerHeight + 2 + 16 + 16 + 16 + 68) * html2pdfOverlay.querySelectorAll('.widgets__canvas').length,
          windowWidth: containerWidth + 16,
          windowHeight: 656,
          scale: 2,
        }
      })
      .then(() => {
        html2pdfOverlay.querySelector('body').style.fontSize = "1.6rem"

        // We reset all scaling here so that the fake canvas adjusts to the "true" size of the dashboard.
        html2pdfOverlay.querySelectorAll('[id*=dashboard-widget-container]').forEach((el) => {
          el.style.transform = ''
          el.style.height = container.dataset.height + 'px'
        })

        html2pdfOverlay.querySelectorAll('.table-container').forEach((el) => {
          el.parentElement.style.overflow = "hidden"
        })

        html2pdfOverlay.querySelector('.html2pdf__container').style.width = "auto"

        html2pdfOverlay.querySelectorAll(
          'td span, th a, .pagination li, .pagination input, .metric__title, .metric__value, .metric__comparison'
        ).forEach((el) => {
          el.style.position = "relative"
          el.style.display = "block"
          el.style.top = "-0.2em"
          el.style.height = "1.2em"
          el.style.lineHeight = "1.2em"
        })
      })
      // html2pdf fills this gap with all the necessary steps, like converting to image etc.
      .save(document.querySelector('input[name=filename]').value || this.element.dataset.filename)
      .then(() => {
        placeholder.remove()
        this.element.style.color = null
      })
  }

  createPlaceholder() {
    const placeholder = document.createElement('template')
    placeholder.innerHTML = `
      <div class='placeholder-scr--inline'>
        <i class="fad fa-spinner-third fa-spin bg-blue text-white"></i>
      </div>
    `.trim()
    return placeholder.content.firstChild
  }
}
