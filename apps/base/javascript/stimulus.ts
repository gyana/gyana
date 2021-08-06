import { Application } from 'stimulus'
import { definitionsFromContext } from 'stimulus/webpack-helpers'

const application = Application.start()

// for webpack, arguments to require.context are string literals
// https://webpack.js.org/guides/dependency-management/#requirecontext

const CONTEXTS = [
  require.context('../../base/javascript/controllers', true, /\.js$/),
  require.context('../../columns/javascript/controllers', true, /\.js$/),
  require.context('../../nodes/javascript/controllers', true, /\.js$/),
  require.context('../../uploads/javascript/controllers', true, /\.js$/),
  require.context('../../web/javascript/controllers', true, /\.js$/),
  require.context('../../widgets/javascript/controllers', true, /\.js$/),
  require.context('../../workflows/javascript/controllers', true, /\.js$/),
]

for (const context of CONTEXTS) application.load(definitionsFromContext(context))
