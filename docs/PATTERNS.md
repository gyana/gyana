# Patterns

Description of patterns I've started using and building out in the app.

## React wrapped (templatable) HTML

For the lack of a better name, what this essentially means is that a custom WebElement mounting a React component can have plain HTML inside allowing us to use Django's templating engine to decide the content of a React wrapped element.

### What it do

A good example of a use case is the [GyWidget](../templates/javascript/GyWidget.tsx) component. This mounts a ReactRnd instance that allows the user to move and resize an HTML element freely. The children of such a component get no benefit from being React-ified, allowing the GyWidget to mount its children simply as HTML can have us write our HTML in the Django templating stage.

**The essence of this pattern** is a WebElement mounting a React component and passing its children as raw HTML into the React component. The children are out of the scope of React this way.

### Benefits:

- No need to pass JSON data to populate React child components
- No need to React-ify all html within a React wrapper component
- Fully leverage Django's templating engine, more reusability of UI code
- Backend remains the owner of business logic

### Downsides:

- Only makes sense when a wrapper requires React, for more complex components that require a full React hierarchy this won't work

## Celery progress flows

Dynamic async flows with quick user feedback and feel for progress.

### What it do

This is a combination of Celery tasks and Celery-progress that listens to tasks their progress. `celery_progress_controller.js` handles html that can listen to a celery task and updates state accordingly. It's a purely business logic solution, meaning that the UI that is built around it can be anything. Taking inspiration from Celery-progress, but without the outdated UI they introduced with it.

An example of its usage can be found for all the Integrations. Using TurboStreams and redirects different stages of any arbitrary flow can trigger new stages or full redirects to other pages (when a flow is complete for example). The Integration connector creation flow uses a set of endpoints and one template that renders differently per endpoint. Its possible to track a linear progression of the flow by following responses from different endpoints.

### Benefits:

- Quick feedback loop for users, longer tasks are deferred to celery, server responses are therefore quick
- Flexibility in multistage flows (valuable for integration creation)

### Downsides:

- Linear progress through urls not trivial to follow/remember
- Uses polling for celery tasks, Django Channels might be nice here instead
- Can end up having us write many one-off tasks
