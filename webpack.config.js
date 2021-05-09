const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const TsconfigPathsPlugin = require("tsconfig-paths-webpack-plugin");

module.exports = {
  resolve: {
    extensions: [".ts", ".tsx", ".js", ".jsx"],
    plugins: [new TsconfigPathsPlugin()],
  },
  entry: {
    style: "./assets/styles/style.scss",
    app: "./assets/javascript/app.ts",
    teams: "./assets/javascript/teams/teams.tsx",
    "edit-team": "./assets/javascript/teams/edit-team.tsx",
    stimulus: "./assets/javascript/stimulus.ts",
    dataflow: "./apps/dataflows/javascript/app.tsx",
  },
  output: {
    path: path.resolve(__dirname, "./static"),
    filename: "js/[name]-bundle.js",
    library: ["SiteJS", "[name]"],
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx|js|jsx)$/,
        exclude: /node_modules/,
        loader: "babel-loader",
        options: {
          presets: [
            "@babel/env",
            "@babel/preset-react",
            "@babel/preset-typescript",
          ],
          plugins: [
            "@babel/plugin-proposal-class-properties",
            "@babel/plugin-transform-runtime",
          ],
        },
      },
      {
        test: /\.scss$/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
      },
    ],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "css/[name].css",
    }),
  ],
};
