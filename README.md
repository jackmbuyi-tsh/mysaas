# Uzuritech (mysaas)

Multi-tenant management platform for schools and hotels, built for small
organizations in the DR Congo. *Uzuri* means beauty or excellence in Swahili.

One codebase serves every client. Each school or hotel gets its own subdomain
(`ecole1.uzuritech.com`, `hotel1.uzuritech.com`) and only ever sees its own data.

> **Status:** early scaffolding. This is a rewrite in Django of a working
> PHP/MySQL prototype.

## What's here

| App | Contents |
|---|---|
| `tenants` | `Tenant` model, subdomain middleware, tenant-scoped base model, shared `Employee` |
| `schools` | Buildings, school years, classes, pupils, parents, courses, grades |
| `hotels` | Rooms, guests, reservations, invoices, expenses |

Payments are out of scope for the first release.

## How tenant isolation works

Data leaking between clients is the main risk in a multi-tenant app, and it
happened in the prototype: a test with two schools showed one school's data
inside the other. This version guards against it at the model layer:

1. `TenantMiddleware` reads the subdomain and sets the current tenant for the request.
   Unknown or inactive subdomains return 404.
2. Every school and hotel table inherits `TenantScopedModel`, which adds a `tenant`
   foreign key.
3. Its default manager (`objects`) filters every query by the current tenant.
   **If no tenant is set, it raises an error** instead of returning all rows.
4. `save()` fills in the tenant automatically and refuses to write a row that
   belongs to a different tenant.
5. Platform-level code (admin, scripts) must opt in explicitly with `Model.unscoped`
   or `tenant_context(tenant)`.

The tests in `tenants/tests.py` check each of these rules.

## Running it locally

Requires Python 3.12+ and MariaDB 10.5+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# MariaDB
mysql -u root -p -e "CREATE DATABASE uzuritech CHARACTER SET utf8mb4;
  CREATE USER 'uzuritech'@'localhost' IDENTIFIED BY 'change-me';
  GRANT ALL ON uzuritech.* TO 'uzuritech'@'localhost';"
export DB_PASSWORD=change-me     # see .env.example for all settings

python manage.py migrate
python manage.py seed_demo       # two demo schools and one demo hotel
python manage.py runserver
```

Then open:

- http://localhost:8000: platform home
- http://ecole1.localhost:8000 and http://ecole2.localhost:8000: demo schools
- http://hotel1.localhost:8000: demo hotel

Modern browsers resolve `*.localhost` to your machine, so no hosts-file
changes are needed.

To try it without MariaDB, prefix commands with `DB_ENGINE=sqlite`.

## Tests

```bash
DB_ENGINE=sqlite python manage.py test
```

## Stack

Python 3.12, Django 5.1, MariaDB (via PyMySQL, a pure-Python driver, so no C
build tools are needed), server-rendered HTML.

## Licence

MIT. See [LICENSE](LICENSE).
