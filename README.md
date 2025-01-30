![Alt Text](gyana.jpg)

<p align="center"><em>Open source, no-code business intelligence built on Django</em></p>

---

**Documentation**: <a href="https://gyana.github.io/docs" target="_blank">https://gyana.github.io/docs</a>

**Source Code**: <a href="https://github.com/gyana/gyana" target="_blank">https://github.com/gyana/gyana</a>

---

Gyana is a toolkit for building business intelligence tools, written in Django.

Why Gyana? In our experience, traditional BI tools lack the flexibility most businesses need, but building a modern data stack is often overkill.

Gyana solves this in two ways:

1. A set of no-code abstractions that provide close to the flexibility of code solutions (but without associated headaches)
2. An extensible, open source codebase where it's easy to add custom business logic (think: formulas, nodes or entire features) in idiomatic Django

Using Gyana, you can deliver a data analytics experience tailored to your needs of your business, stakeholders or clients, without wasting time in repetitive coding tasks.

## Features

- Modern data stack "in a box" - no-code interface for ELT, writing SQL, building dashboards and automating pipelines
- Fully-featured collaboration system for internal teams or managing clients
- Opinionated, high quality, low Javascript (think: HTMX + AlpineJS) codebase built on idiomatic Django
- Fully open source, self-host wherever you want

## Getting started

You can run Gyana locally <5 mins with docker:

```bash
git clone git@github.com:gyana/gyana.git
cd gyana
docker build -f Dockerfile.dev -t gyana:dev .
docker compose up
```

Open your browser at http://localhost:8000.

**Note**: For the signup, your activation email will be logged in the terminal 😊

For more detailed instructions on local developmnet, see our [DEVELOPMENT](https://github.com/gyana/gyana/blob/main/DEVELOPMENT.md) guide.

## License

This project is licensed under the terms of the MIT license.
