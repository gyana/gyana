const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const TsconfigPathsPlugin = require('tsconfig-paths-webpack-plugin')

module.exports = {
  resolve: {
    extensions: ['.ts', '.tsx', '.js'],
    plugins: [new TsconfigPathsPlugin()],
  },
  entry: {
    automate: './apps/projects/javascript/automate-flow.tsx',
    base: './apps/base/javascript/index.ts',
    columns: './apps/columns/javascript/index.ts',
    components: './apps/base/javascript/components.ts',
    dashboards: './apps/dashboards/javascript/index.ts',
    fontawesome: './apps/base/styles/vendors/fontawesome.css',
    stimulus: './apps/base/javascript/stimulus.ts',
    style: './apps/base/styles/style.scss',
    website: './apps/web/styles/website.scss',
    tailwind: './apps/base/styles/vendors/tailwind.pcss',
    'web-integration-demo': './apps/web/javascript/integration-demo.tsx',
    'web-workflow-demo': './apps/web/javascript/workflow-demo.tsx',
    'web-dashboard-demo': './apps/web/javascript/dashboard-demo.tsx',
    widgets: './apps/widgets/javascript/index.ts',
    workflows: './apps/workflows/javascript/dnd-flow.tsx',
  },
  output: {
    path: path.resolve(__dirname, './static'),
    filename: 'js/[name]-bundle.js',
    library: ['SiteJS', '[name]'],
  },
  devtool: 'source-map',
  module: {
    rules: [
      {
        test: /\.(ts|tsx|js|jsx)$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        // Uses .babelrc for options
        // options: {}
      },
      {
        test: /\.scss$/i,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader'],
      },
      {
        test: /\.(p)?css$/i,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader'],
      },
      {
        test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?(#.*)?$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'fonts/',
            publicPath: '../fonts',
          },
        },
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: 'css/[name].css',
    }),
  ],
}
