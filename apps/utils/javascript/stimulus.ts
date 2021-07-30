import { Application } from 'stimulus'
import { definitionsFromContext } from 'stimulus/webpack-helpers'

const application = Application.start()

const APPS = [
  'columns',
  'dashboards',
  'integrations',
  'nodes',
  'utils',
  'web',
  'widgets',
  'workflows',
]

for (const app of APPS) {
  const context = require.context(`../../${app}/javascript/controllers`, true, /\.js$/)
  application.load(definitionsFromContext(context))
}
