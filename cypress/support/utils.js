import fixtures from '../fixtures/fixtures.json'

export const getModelStartId = (modelname) =>
  Math.max(
    ...fixtures.filter((fixture) => fixture.model == modelname).map((fixture) => fixture.pk)
  ) + 1

// pending and ready integrations for the main test project

const projectId = 1

export const readyIntegrations = fixtures.filter(
  (fixture) =>
    fixture.model == 'integrations.integration' &&
    fixture.fields.ready &&
    fixture.fields.project == projectId
).length

export const pendingIntegrations = fixtures.filter(
  (fixture) =>
    fixture.model == 'integrations.integration' &&
    !fixture.fields.ready &&
    fixture.fields.project == projectId
).length
