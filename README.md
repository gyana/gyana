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
