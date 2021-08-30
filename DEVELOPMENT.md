# Development

## Prerequisites

Packages and software required to develop the tool. Install via homebrew, unless indicated otherwise.

Required:

- just
- direnv
- poetry
- yarn
- watchexec
- postgres 13 (https://postgresapp.com/)
- redis 6 (https://jpadilla.github.io/redisapp/)

Optional / Recommended:

- heroku

We have a recommended list of extensions for developing in VSCode.

## Setup

Authorize direnv to configure your local environment:

```bash
direnv allow .
```

Install all required python and node dependencies:

```bash
poetry install
yarn install
```

Create a local database and run migrations on it:

```bash
createdb gyana
just migrate
just seed
```

Make sure to authenticate using gcloud and generate the relevant env variables:

```bash
gcloud auth login
gcloud config set project gyana-1511894275181
just env # decrypt secrets stored in repository
```

## Develop

At this point you should be able to run the app. Run Django development server,
celery backend for tasks and webpack to bundle all the client side code and styles.
Make sure that Postgres and Redis servers are running:

```bash
just dev
just celery
yarn build:watch
```

Bootstrap a new CRUDL Django app with `just startapp`.

## Test

Run your app in development mode and open the cypress UI:

```
yarn cypress:open
```

The database is seeded with fixtures, and reset before each test. To modify the
fixtures, manually make the changes in the UI and dump them.

```bash
# remember to re-seed the database to initial state
just cypress-setup
# ...make changes...
just cypress-fixtures
```

## QA

Run the entire e2e test suite locally, and view the list of failed tests. You can
review screenshots and videos in the cypress folder to spot easy fixes:

```
yarn cypress:run
yarn cypress:failed
```

Manually fix failed tests in the UI and re-run the tests suite to confirm.

## Deployment

For more in-depth information see [DEPLOYMENT.md](DEPLOYMENT.md)

Run `just export` and push to main. View errors on
[Heroku](https://dashboard.heroku.com/apps/gyana-mvp).

## Javascript

## Philosophy

> Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away.

We believe it is possible for a small team to build world-class software
that customers love, fast, by being smart, efficient and practical about how
we do things.

Mariusz has documented our approach to [styles](assets/styles/STYLES.md).

David has written a [blog](https://davidkell.substack.com/p/davids-opinionated-guide-for-building)
post about building MVPs fast with Django.

Our application architecture is driven by two ideas:

- Decouple features into separate Django apps with no more than 1-2k lines of code,
  typically built around a single core model
- Make the layout of each app as predictable as possible, including file names
  and code structure

## Inspiration

- Interactive pages with less javascript - [Hotwire](https://hotwire.dev/)
- Our boilerplate generator - [SaaS Pegasus](https://www.saaspegasus.com/)
- Using JS in Django - [Modern JavaScript for Django Developers](https://www.saaspegasus.com/guides/modern-javascript-for-django-developers/)
- Pragmatic Django for fast development - [Django for Startup Founders](https://alexkrupp.typepad.com/sensemaking/2021/06/django-for-startup-founders-a-better-software-architecture-for-saas-startups-and-consumer-apps.html)
- Django docs - [Django documentation](https://docs.djangoproject.com/en/3.2/)
- Django packages reference - [Django Packages](https://djangopackages.org/)
- Detailed docs for class based views - [Classy CBV](https://ccbv.co.uk/)
- Prototyping layouts - [Tailwind CSS](https://tailwindcss.com/)
- How we do CSS classes - [BEM — Block Element Modifier](http://getbem.com/)
