---
name: laravel-migrations
description: How to draft, name, write, and run Laravel database migrations for this project's backend — the migration file template, artisan commands, and safety rules used by the planning and migration-management agents
---

# Laravel Migrations

Authoritative reference for **database schema migrations** on the Laravel backend. Two different agents read this skill for two different purposes:

- **`sub-plan-draft`** reads it to *draft* a migration's file name and full content as part of an implementation plan, for human review before any code is written.
- **`sub-manage-migrations`** reads it to *materialize* that drafted content into a real file, validate it, and — once a human has approved it — actually run it.

Both must follow the same conventions below so a migration drafted in the plan and the migration that ends up on disk are identical.

## File Naming

One migration file per logical schema change (one new table, or one set of related column/index changes to an existing table), named:

```
database/migrations/{timestamp}_{verb}_{table}_table.php
```

- `{timestamp}` — `YYYY_MM_DD_HHMMSS`, later than the timestamp of the latest existing migration touching that table (never assume — check `database/migrations/` for the real latest one first).
- `{verb}` — `create` for a new table, or a descriptive verb for an alteration — `add_priority_to`, `drop_status_from`, `add_index_to`, etc.
- `{table}` — the plural `snake_case` table name.

Examples: `2024_01_15_103000_create_tasks_table.php`, `2024_01_15_104500_add_priority_to_tasks_table.php`.

## Migration File Template

Every migration is a single anonymous class with both `up()` (apply) and `down()` (reverse) — **a migration without a working `down()` is a defect, not an acceptable shortcut.**

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('tasks', function (Blueprint $table): void {
            $table->id();
            $table->string('title');
            $table->text('description')->nullable();
            $table->string('status')->default('pending');
            $table->string('priority')->default('medium');
            $table->timestamp('due_date')->nullable();
            $table->timestamp('completed_at')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('tasks');
    }
};
```

For an **alteration** to an existing table, use `Schema::table()` in `up()` and reverse exactly that change (not the whole table) in `down()`:

```php
public function up(): void
{
    Schema::table('tasks', function (Blueprint $table): void {
        $table->string('priority')->default('medium')->after('status');
    });
}

public function down(): void
{
    Schema::table('tasks', function (Blueprint $table): void {
        $table->dropColumn('priority');
    });
}
```

Column/table naming, types, and defaults must match the conventions in `.github/skills/laravel-backend-standards/SKILL.md` (plural `snake_case` tables, `snake_case` columns) and the columns actually defined in the ticket's `PLAN`/`MODEL` section — never invent a column that isn't in one of those two places.

## Commands

| Purpose | Command |
|---------|---------|
| Scaffold a new migration file (optional — writing the file directly per the template above is equally valid) | `./vendor/bin/sail artisan make:migration {name} --table={table}` (or `--create={table}` for a new table) |
| Dry run — print the SQL without touching the database | `./vendor/bin/sail artisan migrate --pretend` |
| Apply pending migrations | `./vendor/bin/sail artisan migrate` |
| Confirm which migrations have run | `./vendor/bin/sail artisan migrate:status` |
| Confirm a migration's schema change actually landed (table/columns exist as expected) | `./vendor/bin/sail artisan tinker --execute="var_dump(Schema::hasTable('{table}'), Schema::getColumnListing('{table}'));"` |
| Rollback/reapply smoke test (proves `down()` genuinely reverses `up()`) | `./vendor/bin/sail artisan migrate:rollback --step=1` then `./vendor/bin/sail artisan migrate` |

`--pretend` and the rollback smoke test both require a real (local/dev) database connection configured in `.env` — they do not work against a purely hypothetical schema.

After `migrate:status` confirms a migration ran, use the `tinker` command above (via Laravel's own `Schema` facade, not a raw SQL client) to confirm the actual table/columns match what the migration was supposed to produce — swap in the real table name and, when only specific columns matter, check for those with `Schema::hasColumn('{table}', '{column}')` instead of listing all of them.

**Always run these commands exactly as written above — `./vendor/bin/sail artisan ...`, never bare `php artisan ...` — with no `--database=` or `--env=` flag and no inline `DB_CONNECTION`/`DB_DATABASE` override.** Every command must use whatever connection this project's own configured Laravel connection already resolves to for the current branch — never force `sqlite` (in-memory or file-based) or any other connection, and never target a specific environment by name, to make a dry run/migrate/rollback "easier" or faster. If the configured connection isn't reachable, that's a blocker to report, not something to work around by swapping in a different database or environment.

## Safety Rules

- **Never edit a migration that has already shipped** to `main`/`develop` (or any shared/deployed environment) — write a new migration to make the further change instead. Editing a migration created earlier within this same unmerged ticket/branch is fine.
- **Never run a migration against a production or shared staging database** — only the local/dev database configured for the current branch.
- **Flag every destructive change explicitly** (a dropped column, a dropped table, a narrowed column type) — don't bury it in a routine-looking diff; the human reviewing the plan or the migration draft needs to see it called out.
- **Never bury a data migration/backfill inside a schema migration silently** — a backfill over a large table can lock it; call it out so timing can be planned deliberately (e.g. as a queued job instead).
- **Every migration must be reversible.** An empty or no-op `down()` — or one that doesn't actually undo `up()` — is a defect.
- **Never invoke a raw database-shell command** (`mysql -e`, `psql -c`, `sqlite3`, or similar) to inspect or verify schema state — for example, never run `./vendor/bin/sail mysql -e "DESCRIBE {table};"`. Use `migrate:status` and the `tinker`-based `Schema` check above — both go through Laravel's own configured connection and don't require guessing at a client/credentials.

## For `sub-plan-draft` specifically

Draft the full file content (not a description) directly into the plan's `MIGRATIONS` section, using the template above, grounded in the schema you've verified actually exists (via `search/fileSearch` on `database/migrations/*_{table}*` or a graph query) plus the plan's own `MODEL` section.

## For `sub-manage-migrations` specifically

When `PLAN` already contains drafted migration content, materialize it verbatim (adjusting only the timestamp if a newer migration has landed for that table since drafting) rather than redesigning it. Only design fresh when `PLAN` omitted a needed migration — and flag that gap back to the calling agent when you do.
