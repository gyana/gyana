const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const TsconfigPathsPlugin = require('tsconfig-paths-webpack-plugin')

module.exports = {
  resolve: {
    extensions: ['.ts', '.tsx', '.js'],
    plugins: [new TsconfigPathsPlugin()],
  },
  entry: {
    fontawesome: './apps/base/styles/vendors/fontawesome.css',
    style: './apps/base/styles/style.scss',
    website: './apps/web/styles/website.scss',
    tailwind: './apps/base/styles/vendors/tailwind.pcss',
    'web-integration-demo': './apps/web/javascript/integration-demo.tsx',
    'web-workflow-demo': './apps/web/javascript/workflow-demo.tsx',
    'web-dashboard-demo': './apps/web/javascript/dashboard-demo.tsx',
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
