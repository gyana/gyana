# Gyana styling

This section will be extended in the future, for now I reccomend reading:

- <https://www.easeout.co/blog/2020-08-25-structuring-your-sass-projects/>
- <https://css-tricks.com/bem-101/>

A great file to get to grips with the BEM methadology is [navbar.scss](components/_navbar.scss)

## React styling

React components should use the individual stylesheets located in the same directory as the
component, importing the stylesheet will compile the SCSS normally and help in co-locating the
styles.

React components should also follow BEM methadology as scoped styles are not implemented right now.
