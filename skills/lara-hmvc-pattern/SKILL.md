---
name: laravel-hmvc-pattern
description: Laravel HMVC (Hierarchical Model-View-Controller) pattern skill for a modular Laravel API backend where feature code lives in `Modules/{Name}/` (Http/Controllers, Models, Exceptions, Services) and shared code stays in `app/`. Use this skill whenever the user is working in a Laravel project with a `Modules/` directory or mentions HMVC, modules, modular Laravel, "create a module", "add a controller/service/model/exception to the Auth or User module", module routes, or asks where a Laravel file should live in this structure. Also use it when scaffolding a new Laravel API feature, reviewing Laravel code for architecture/folder-placement violations, or generating tests, factories, migrations or routes that must fit this layout, even if the user never says "HMVC".
---

# Laravel HMVC Pattern

A Laravel API backend split into **self-contained feature modules** under `Modules/`, with truly shared code kept in `app/`. Each module owns its controllers, models, exceptions and services. Routes, migrations, factories, seeders, config and tests stay in Laravel's standard top-level locations.

The point of the pattern: a feature's code is found in one place, modules talk to each other through narrow seams (Services), and `app/` stays small enough that nobody wonders what lives there.

## Target structure

```
backend/
├── app/
│   ├── Http/Controllers/        ← Common API controllers (base Controller, health check, etc.)
│   ├── Models/                  ← Shared models used by 2+ modules
│   ├── Exceptions/              ← Global handler + shared base exceptions
│   └── Middleware/              ← ALL middleware lives here (Http/Middleware)
├── Modules/                     ← Feature modules (sibling of app/)
│   ├── Auth/
│   │   ├── Http/Controllers/    ← Module API controllers
│   │   ├── Models/              ← Module-owned models
│   │   ├── Exceptions/          ← Module-specific exceptions
│   │   └── Services/            ← Business logic
│   └── User/
│       ├── Http/Controllers/
│       ├── Models/
│       ├── Exceptions/
│       └── Services/
├── config/
├── database/{migrations,factories,seeders}/
├── routes/{api.php,web.php,console.php}
├── tests/{Unit,Feature,TestCase.php}
├── storage/  public/index.php  composer.json  artisan  .env  .env.example
```

`Modules/` sits next to `app/`, not inside it, so its root namespace is `Modules\`. If the user's repo actually has it at `app/Modules/`, use `App\Modules\` instead and adjust the autoload entry; everything else is unchanged.

## Where does this file go? (decision rules)

Work through these in order when placing any new code:

| Code | Location | Why |
|---|---|---|
| Controller for one feature | `Modules/<M>/Http/Controllers/` | Feature-owned HTTP surface |
| Controller used by no specific feature (health, base `Controller`) | `app/Http/Controllers/` | Shared |
| Business logic, DB orchestration, transactions | `Modules/<M>/Services/` | Keeps controllers thin and logic testable |
| Eloquent model owned by one module | `Modules/<M>/Models/` | Module owns its data |
| Eloquent model needed by 2+ modules with no clear owner | `app/Models/` | Avoids circular module dependencies |
| Exception specific to one feature | `Modules/<M>/Exceptions/` | Stays with the code that throws it |
| Base/global exception, handler | `app/Exceptions/` | Shared |
| Middleware (always) | `app/Http/Middleware/` | Single registry; never inside a module |
| Routes | `routes/api.php` (grouped per module) | One place to see the whole API |
| Migrations, factories, seeders | `database/...` (top-level) | Laravel tooling expects them there |
| Tests | `tests/Unit/<Module>/`, `tests/Feature/<Module>/` | Mirrors module layout |

If a request needs a folder the structure doesn't have (Form Requests, API Resources, Policies, Enums), the natural home is `Modules/<M>/Http/Requests/`, `Http/Resources/`, `Policies/`, `Enums/`. These are reasonable extensions, but mention to the user that you're adding a folder beyond the agreed layout rather than doing it silently.

## Layer responsibilities

**Controller → Service → Model**, one direction only.

- **Controllers** parse/validate input, call exactly one Service method, return a JSON response. No queries, no business rules, no transactions.
- **Services** hold business logic. They receive plain data (arrays/DTO-ish scalars), not `Request` objects, so they can be called from controllers, console commands, jobs and tests alike. Inject via constructor.
- **Models** define schema mapping, relationships, casts, scopes. No HTTP concerns.
- **Exceptions** are thrown by Services, rendered to HTTP by the global handler (see Appendix A, section 5).

## Cross-module rules

These keep modules from turning back into a ball of mud:

1. A module may call **another module's Service**. It should not call another module's Controller, and should avoid reaching into another module's Model for behavior. Reading a relationship to a model from another module is acceptable.
2. No circular dependencies. If Auth needs User and User needs Auth, extract the shared piece into `app/` (a shared model or a contract).
3. Module code may use anything in `app/`. `app/` must never import from `Modules/` (except `routes/api.php`, which wires everything together, and config entries like the auth user model).
4. Middleware never lives in a module; reference it from `app/Http/Middleware` by alias in routes.

## Namespaces and autoloading

Pattern: `Modules\<Module>\<Folder>\<Class>`, for example `Modules\Auth\Services\AuthService`.

`composer.json` needs the PSR-4 entry, then `composer dump-autoload`:

```json
"autoload": {
  "psr-4": {
    "App\\": "app/",
    "Modules\\": "Modules/",
    "Database\\Factories\\": "database/factories/",
    "Database\\Seeders\\": "database/seeders/"
  }
}
```

Laravel's `artisan make:*` commands cannot target `Modules/`. Either use the scaffold script in Appendix B or create files by hand with the correct namespace. Don't run `make:controller` and then move files without fixing the namespace.

## Creating a new module

Use the scaffold script from Appendix B. Save it as `make-module.sh` (or run it inline) and execute it from the `backend/` directory. It creates the folder skeleton plus a starter controller and service:

```bash
bash make-module.sh Billing
```

Then do the manual wiring the script prints at the end:
1. Add the module's route group to `routes/api.php`.
2. Add migrations in `database/migrations/`, a factory in `database/factories/`.
3. Add tests under `tests/Unit/Billing` and `tests/Feature/Billing`.

Module names are singular PascalCase (`Auth`, `User`, `Invoice`), matching the folder and namespace exactly.

## Routing

All routes stay in `routes/api.php`, versioned, with one group per module. Import controllers with aliases only when two modules share a class name (e.g. both have `ProfileController`).

```php
use Modules\Auth\Http\Controllers\AuthController;
use Modules\User\Http\Controllers\UserController;

Route::prefix('v1')->group(function () {
    Route::prefix('auth')->group(function () {
        Route::post('login', [AuthController::class, 'login']);
        Route::post('logout', [AuthController::class, 'logout'])->middleware('auth:sanctum');
    });

    Route::middleware('auth:sanctum')->prefix('users')->group(function () {
        Route::get('/', [UserController::class, 'index']);
        Route::get('{user}', [UserController::class, 'show']);
    });
});
```

When a new API version appears, add a sibling `Route::prefix('v2')` group; keep v1 controllers working until deprecated.

## Models, factories and migrations

- Migrations stay one-file-per-change in `database/migrations/`, even for module-owned tables. Name tables conventionally; optionally prefix with the module name if tables could collide.
- Factories live in `database/factories/`, but Laravel's factory-name guessing assumes `App\Models`. In module models, declare the factory explicitly with `newFactory()` (template in Appendix A, section 4).
- If `config/auth.php` points the user provider at a module model, use the full `Modules\User\Models\User::class`.
- Pick one owner per table. Other modules read it via a relationship or the owner's Service.

## Testing

- `tests/Unit/<Module>/` for Services (mock collaborators from other modules).
- `tests/Feature/<Module>/` for HTTP endpoints through `routes/api.php`.
- Test namespaces mirror the module: `Tests\Feature\Auth\LoginTest`.
- Keep the shared `tests/TestCase.php` as the single base class.

## Review checklist

When writing or reviewing code in this layout, verify:

- [ ] Every class sits in the folder the decision table prescribes, and its namespace matches the path.
- [ ] Controllers contain no business logic or direct queries.
- [ ] Middleware is only in `app/Http/Middleware`.
- [ ] No module imports another module's Controller; no `app/` file imports from `Modules/`.
- [ ] Exceptions thrown by Services are mapped to HTTP responses in the handler.
- [ ] New module is autoloadable (`Modules\\` PSR-4 entry present) and its routes are registered.
- [ ] Migration, factory (with `newFactory()`), and tests exist for any new model.

## Appendix A: Code templates

Copy-ready templates for this layout. Namespaces assume `Modules/` is a sibling of `app/`. Examples use the `Auth` and `User` modules. Read the relevant section when you are about to write those files.

Sections: 1. Base controller, 2. Module controller, 3. Service, 4. Module model + factory, 5. Exceptions, 6. Cross-module call, 7. Tests.

### 1. Base controller (shared)

`app/Http/Controllers/Controller.php`

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;

abstract class Controller
{
    protected function success(mixed $data = null, string $message = 'OK', int $status = 200): JsonResponse
    {
        return response()->json([
            'success' => true,
            'message' => $message,
            'data'    => $data,
        ], $status);
    }

    protected function created(mixed $data = null, string $message = 'Created'): JsonResponse
    {
        return $this->success($data, $message, 201);
    }
}
```

Module controllers extend this class so every module returns the same envelope.

### 2. Module controller

`Modules/Auth/Http/Controllers/AuthController.php`

```php
<?php

namespace Modules\Auth\Http\Controllers;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Modules\Auth\Services\AuthService;

class AuthController extends Controller
{
    public function __construct(private readonly AuthService $authService)
    {
    }

    public function login(Request $request): JsonResponse
    {
        $credentials = $request->validate([
            'email'    => ['required', 'email'],
            'password' => ['required', 'string'],
        ]);

        // Controller passes plain data; the Service knows nothing about HTTP.
        $token = $this->authService->login($credentials['email'], $credentials['password']);

        return $this->success(['token' => $token], 'Logged in');
    }

    public function logout(Request $request): JsonResponse
    {
        $this->authService->logout($request->user());

        return $this->success(null, 'Logged out');
    }
}
```

### 3. Service

`Modules/Auth/Services/AuthService.php`

```php
<?php

namespace Modules\Auth\Services;

use Illuminate\Support\Facades\Hash;
use Modules\Auth\Exceptions\InvalidCredentialsException;
use Modules\User\Services\UserService;

class AuthService
{
    public function __construct(private readonly UserService $userService)
    {
    }

    public function login(string $email, string $password): string
    {
        $user = $this->userService->findByEmail($email);

        if (! $user || ! Hash::check($password, $user->password)) {
            throw new InvalidCredentialsException();
        }

        return $user->createToken('api')->plainTextToken;
    }

    public function logout($user): void
    {
        $user->currentAccessToken()?->delete();
    }
}
```

Use `DB::transaction(fn () => ...)` inside Services, never in controllers.

### 4. Module model + factory

`Modules/User/Models/User.php`

```php
<?php

namespace Modules\User\Models;

use Database\Factories\UserFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory;

    protected $fillable = ['name', 'email', 'password'];

    protected $hidden = ['password', 'remember_token'];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password'          => 'hashed',
        ];
    }

    // Laravel guesses factories under App\Models only. Be explicit for modules.
    protected static function newFactory(): UserFactory
    {
        return UserFactory::new();
    }
}
```

`database/factories/UserFactory.php`

```php
<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Modules\User\Models\User;

/** @extends Factory<User> */
class UserFactory extends Factory
{
    protected $model = User::class;

    public function definition(): array
    {
        return [
            'name'     => fake()->name(),
            'email'    => fake()->unique()->safeEmail(),
            'password' => 'password', // hashed by the model cast
        ];
    }
}
```

When the user model moves to a module, update `config/auth.php`:

```php
'providers' => [
    'users' => [
        'driver' => 'eloquent',
        'model'  => Modules\User\Models\User::class,
    ],
],
```

### 5. Exceptions

Shared base, `app/Exceptions/ApiException.php`:

```php
<?php

namespace App\Exceptions;

use Exception;
use Illuminate\Http\JsonResponse;

class ApiException extends Exception
{
    protected int $status = 400;

    public function render(): JsonResponse
    {
        return response()->json([
            'success' => false,
            'message' => $this->getMessage(),
        ], $this->status);
    }
}
```

Module exception, `Modules/Auth/Exceptions/InvalidCredentialsException.php`:

```php
<?php

namespace Modules\Auth\Exceptions;

use App\Exceptions\ApiException;

class InvalidCredentialsException extends ApiException
{
    protected int $status = 401;

    public function __construct(string $message = 'Invalid credentials')
    {
        parent::__construct($message);
    }
}
```

Because `ApiException` defines `render()`, Laravel renders it automatically. No handler changes needed per module. Add a handler entry only for third-party exceptions (e.g. `ModelNotFoundException` → 404). In Laravel 11+ that goes in `bootstrap/app.php` under `->withExceptions(...)`; in Laravel 10 and earlier, in `app/Exceptions/Handler.php`.

### 6. Cross-module call

Call the other module's Service via constructor injection (see `AuthService` above calling `UserService`). Do not instantiate another module's Controller or duplicate its queries.

`Modules/User/Services/UserService.php`

```php
<?php

namespace Modules\User\Services;

use Modules\User\Models\User;

class UserService
{
    public function findByEmail(string $email): ?User
    {
        return User::where('email', $email)->first();
    }
}
```

### 7. Tests

Feature, `tests/Feature/Auth/LoginTest.php`:

```php
<?php

namespace Tests\Feature\Auth;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Modules\User\Models\User;
use Tests\TestCase;

class LoginTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_login(): void
    {
        $user = User::factory()->create(['password' => 'secret123']);

        $this->postJson('/api/v1/auth/login', [
            'email'    => $user->email,
            'password' => 'secret123',
        ])->assertOk()->assertJsonPath('success', true);
    }

    public function test_invalid_credentials_return_401(): void
    {
        $this->postJson('/api/v1/auth/login', [
            'email'    => 'nobody@example.com',
            'password' => 'wrong',
        ])->assertStatus(401);
    }
}
```

Unit, `tests/Unit/Auth/AuthServiceTest.php`, mocking the other module's Service:

```php
<?php

namespace Tests\Unit\Auth;

use Mockery;
use Modules\Auth\Exceptions\InvalidCredentialsException;
use Modules\Auth\Services\AuthService;
use Modules\User\Services\UserService;
use Tests\TestCase;

class AuthServiceTest extends TestCase
{
    public function test_login_throws_when_user_missing(): void
    {
        $users = Mockery::mock(UserService::class);
        $users->shouldReceive('findByEmail')->andReturn(null);

        $this->expectException(InvalidCredentialsException::class);

        (new AuthService($users))->login('x@example.com', 'pw');
    }
}
```

## Appendix B: Module scaffold script

Run from the Laravel root (the directory containing `artisan`). Validates the module name, refuses to overwrite an existing module, creates the folder skeleton, writes a starter controller and service, and prints the manual wiring steps.

```bash
#!/usr/bin/env bash
# Scaffold a new HMVC module. Run from the Laravel project root (the directory containing artisan).
# Usage: make-module.sh <ModuleName>
set -euo pipefail

NAME="${1:-}"
ROOT="Modules"

if [[ -z "$NAME" ]]; then
  echo "Usage: $0 <ModuleName>" >&2
  exit 1
fi
if [[ ! "$NAME" =~ ^[A-Z][A-Za-z0-9]*$ ]]; then
  echo "Module name must be PascalCase (e.g. Billing, Invoice)." >&2
  exit 1
fi
if [[ ! -f artisan ]]; then
  echo "Run this from the Laravel root (artisan not found in $(pwd))." >&2
  exit 1
fi

BASE="$ROOT/$NAME"
if [[ -e "$BASE" ]]; then
  echo "Module $NAME already exists at $BASE" >&2
  exit 1
fi

mkdir -p "$BASE/Http/Controllers" "$BASE/Models" "$BASE/Exceptions" "$BASE/Services"
touch "$BASE/Models/.gitkeep" "$BASE/Exceptions/.gitkeep"

cat > "$BASE/Services/${NAME}Service.php" <<PHP
<?php

namespace Modules\\$NAME\\Services;

class ${NAME}Service
{
    //
}
PHP

cat > "$BASE/Http/Controllers/${NAME}Controller.php" <<PHP
<?php

namespace Modules\\$NAME\\Http\\Controllers;

use App\\Http\\Controllers\\Controller;
use Illuminate\\Http\\JsonResponse;
use Modules\\$NAME\\Services\\${NAME}Service;

class ${NAME}Controller extends Controller
{
    public function __construct(private readonly ${NAME}Service \$service)
    {
    }

    public function index(): JsonResponse
    {
        return \$this->success([]);
    }
}
PHP

LOWER="$(echo "$NAME" | sed -E 's/([a-z0-9])([A-Z])/\1-\2/g' | tr '[:upper:]' '[:lower:]')"

cat <<MSG
Created module $NAME at $BASE

Next steps:
  1. Ensure composer.json has  "Modules\\\\": "Modules/"  under autoload.psr-4, then: composer dump-autoload
  2. Register routes in routes/api.php:

       use Modules\\$NAME\\Http\\Controllers\\${NAME}Controller;

       Route::prefix('v1/$LOWER')->group(function () {
           Route::get('/', [${NAME}Controller::class, 'index']);
       });

  3. Add migrations in database/migrations/ and factories in database/factories/
  4. Add tests in tests/Unit/$NAME and tests/Feature/$NAME
MSG
```