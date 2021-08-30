# Gyana styling

We have a variety of options for writing CSS styles in this project, generally speaking your choice
of styling should follow this pattern:

- **Use existing components** first (button, card, etc.) as classes.
- **Create/Modify components** when needed (if reusable).
- **Create page-specific stylesheets** when you require specific overwrites for a single page.
- **Use tailwind** as a last resort for extremely specific and one-off cases.

Prototype quickly with tailwind classes, use existing components where possible and then migrate all
tailwind classes to a standalone stylesheet (avoid using `@apply`).

This section will be extended in the future, for now I reccomend reading these:

- <https://www.easeout.co/blog/2020-08-25-structuring-your-sass-projects/>
- <https://css-tricks.com/bem-101/>

## Component styling

Simple, visual components should have their own SCSS stylesheet (see `_button.scss`), following
bootstrap conventions in creating a base style with generated colour variants on top.

## Page styling

TBD

## React styling

React components should use the individual stylesheets located in the same directory as the
component, importing the stylesheet will compile the SCSS normally and help in co-locating the
styles.

React components should also follow BEM methadology as scoped styles are not implemented right now.
