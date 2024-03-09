# Development

## Prerequisites

Packages and software required to develop the tool. Install via homebrew, unless indicated otherwise.

Required:

- just
- direnv
- pyenv (`pyenv install 3.9.14`)
- volta (`curl https://get.volta.sh | bash`)
- watchexec
- redis 6 (`brew services start redis`)
- postgres 13 (https://postgresapp.com/)

Optional / Recommended:

- heroku

We have a recommended list of extensions for developing in VSCode.

## Setup

Authorize direnv to configure your local environment:

```bash
direnv allow .
```

Install pip-tools in local python environment:

```bash
pip install pip-tools
```

Install all required python and node dependencies:

```bash
just update
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
npm run build:watch
```

Bootstrap a new CRUDL Django app with `just startapp`.

## Tests

For pytest, run the individual tests:

```
just test -k {name}
```

For e2e, run the e2e tests:

```
just test-e2e
```

## Profile

Open the [Silk](https://github.com/jazzband/django-silk) [UI](http://localhost:8000/silk)
for per request statistics, SQL profiling and cProfile graphs.

Setup Honeycomb [locally](apps/base/apps.py) to generate traces for
individual HTTP requests.

## QA

Run the pytest test suite:

```
just test
```

Run the entire e2e test suite locally, and view the list of failed tests. You can
run specific tests with the `--headed` flag and `page.pause()` to debug.

Manually fix failed tests and re-run the tests suite to confirm.

## Deployment

For more in-depth information see [DEPLOYMENT.md](DEPLOYMENT.md)

Run `just export` and push to main. View errors on
[Heroku](https://dashboard.heroku.com/apps/gyana-dev).

## Javascript

Instead of building a single page web app, we progressively add interactivity
to pages with different techniques. Choosing which one to use in each situation
is an art but you get better at it over time:

- Turbo Drive - enabled automatically for all clicks and submissions, you might
  need to disable e.g. for external links
- Turbo Frames - lazy loading content and embedding certain UIs (e.g. modals)
- Turbo Streams - update other parts of a page on form submission
- Stimulus - lightweight interactivity
- React - if you need client side state or a library from the React ecosystem -
  wrap in a web component, interact with APIs
- Django widgets - using React or Stimulus
- React wrapped - a React powered web component that has plain HTML (generated
  by Django) as children - see `<gy-widget>`
- Celery Progress - show progress of long running task using the `celery_progress`
  library

## Philosophy

> Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away.

We believe it is possible for a small team to build world-class software,
that customers love, fast, by being smart, efficient and practical about how
we do things.

Mariusz has documented our approach to [styles](apps/base/styles/STYLES.md).

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
