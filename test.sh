#!/bin/bash

# run server in background
./manage.py runserver --settings gyana.settings.cypress &
# run celery in background
DJANGO_SETTINGS_MODULE=gyana.settings.cypress celery -A gyana worker -l info &
# run tests
npx cypress run --spec cypress/integrations/teams.spec.js