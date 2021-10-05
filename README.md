# Gyana

No-Code Data Analytics tool or "Figma meets Domo"
More information can found on [our slab page](https://gyana.slab.com/topics/tech-mlhaecw3)

## Development

For more in-depth instructions refer to [DEVELOPMENT.md](DEVELOPMENT.md)

In short:

```bash
# Create a virtual environment
mkvirtualenv --no-site-packages gyana -p python3

# Install poetry and yarn dependencies
poetry install
yarn install

# Create a local database and run migrations
createdb gyana
python manage.py migrate

# Build the client
yarn build

# Run the app
just dev
```

## Development Principles

- **Better to spend more time writing less code than vice versa**

- **Consistency is golden**

- **Django > Turbo Frame > Turbo Stream > Stimulus > React**
   - **Use Django templating as much as possible**  
      To fully use the power of backend-first html building
   - **Turbo Stream updates > JS dom manipulation**  
      Retains as much HTML/DOM logic in backend code, and leverages the template system nicely. Reusable code FTW
   - **For small interactive snippets use stimulus**  
      Unit level javascript needs are easily solved by generic stimulus controllers
   - **Don't use React when not needed**  
      Keeps the codebase simpler and more comprehensible
   - **Encapsulate React in web components**  
      Consistent way of mounting React components and allows us to use it in the templating engine

- **IDs are sacred**
   - DOM IDs are becoming increasingly more important the more we use the Hotwire stack as it uses IDs in the DOM as mounting points
