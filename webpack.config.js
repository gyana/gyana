const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const TsconfigPathsPlugin = require('tsconfig-paths-webpack-plugin')

module.exports = {
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    plugins: [new TsconfigPathsPlugin()],
  },
  entry: {
    style: './apps/base/styles/style.scss',
    fontawesome: './apps/base/styles/vendors/fontawesome.css',
    tailwind: './apps/base/styles/vendors/tailwind.pcss',
    turbo: './apps/base/javascript/turbo.ts',
    stimulus: './apps/base/javascript/stimulus.ts',
    workflow: './apps/workflows/javascript/app.tsx',
    components: './apps/base/javascript/components.ts',
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
        test: /\.(s)?css$/i,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader', 'sass-loader'],
      },
      {
        test: /\.pcss$/i,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader'],
      },
      {
        test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?(#.*)?$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'fonts/',
            publicPath: '../fonts'
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
