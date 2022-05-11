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
    const html2pdfWorker = html2pdf()
    
    await html2pdfWorker
      .from(document.body)
      .set({
        enableLinks: false,
        jsPDF: {
          compress: true
        },
      })
      // Prepare the "fake" container copy so we can adjust it.
      .toContainer()
      
    // This is the container created by html2pdf when we use .toContainer()
    const html2pdfOverlay = document.querySelector('.html2pdf__overlay');
    const container = html2pdfOverlay.querySelector('#dashboard-widget-container')
    const { height: windowHeight } = html2pdfOverlay.querySelector('.widgets').getBoundingClientRect()
      
    html2pdfWorker
      .set({
        /**
         * There's quite a lot of magic numbering to explain here.
         * 
         * We parse the set dashboard width as an int so that the pdf
         * output is consistent.
         * 
         * 32 is the pixel value of the padding around the dashboard.
         * 
         * windowWidth and windowHeight are set to consistent values, they
         * can potentially be increased at some point for increased quality.
         */
        html2canvas: {
          width: parseInt(container.dataset.width) + 32,
          height: windowHeight + 32,
          windowWidth: 1366,
          windowHeight: 656,
          scale: 2.2,
        }
      })
      .then(() => {
        // We reset all scaling here so that the fake canvas adjusts to the "true" size of the dashboard.
        container.style.transform = ''
        container.style.height = container.dataset.height + 'px'
      })
      // html2pdf fills this gap with all the necessary steps, like converting to image etc.
      .save(this.element.dataset.filename)
  }
}
