import fixtures from '../fixtures/fixtures.json'

export const getModelStartId = (modelname) =>
  Math.max(
    ...fixtures.filter((fixture) => fixture.model == modelname).map((fixture) => fixture.pk)
  ) + 1
