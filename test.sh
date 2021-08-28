#!/bin/bash

# run server in background
./manage.py runserver --settings gyana.settings.cypress &
# run celery in background
DJANGO_SETTINGS_MODULE=gyana.settings.cypress celery -A gyana worker -l info &
# run tests
ELECTRON_RUN_AS_NODE=1 npx cypress run --browser chrome --spec cypress/integrations/teams.spec.js