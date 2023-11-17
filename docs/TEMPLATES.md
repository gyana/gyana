# Templates

How the template hierarchy works:

```
web/base.html (body)
├─ web/base.html (main)
   ├─ teams/base.html (app)
      ├─ teams/settings_base.html (app)
   ├─ projects/base.html (app)
      ├─ projects/settings_base.html (app)
      ├─ integrations/base.html (tab)
         ├─ integrations/detail.html
         ├─ ...
web/site_base.html
```
