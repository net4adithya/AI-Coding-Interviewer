# Implement Remaining Backend Modules

## Goal Description
Complete the backend implementation for the AI Coding Review Platform by adding the missing feature modules: **Interns**, **Assignments**, **Dashboard**, and integrating them into the main application (`AppModule`). This includes DTOs, controllers, services, repositories (where needed), module declarations, and routing with appropriate guards and Swagger documentation. The resulting API will support CRUD operations for Interns and Assignments, and provide aggregated dashboard data for Authorities and Interns.

## User Review Required
> [!IMPORTANT]
> Review the proposed API routes, role/permission guards, and response structures. Confirm if any additional fields or business rules are required (e.g., validation constraints, pagination defaults, or extra dashboard metrics).

## Open Questions
> [!CAUTION]
> - **Interns endpoints**: Should Interns be creatable only by Authorities? Should there be an endpoint to assign an Authority to an Intern?
> - **Assignments creation**: Must the `createdById` (Authority) be derived from the JWT rather than passed in the DTO?
> - **Dashboard data**: Do you need any extra statistics beyond the listed ones (e.g., average assignment difficulty, upcoming deadlines count)?
> - **Pagination defaults**: Preferred default `page` and `limit` values for list endpoints?
> - **Error handling**: Any custom error response format beyond the existing `TransformInterceptor`?

## Proposed Changes
---
### Interns Module
- **[NEW] src/modules/interns/dto/create-intern.dto.ts** – DTO for creating an Intern.
- **[NEW] src/modules/interns/dto/update-intern.dto.ts** – DTO for updating an Intern (extends `PartialType`).
- **[NEW] src/modules/interns/interns.service.ts** – Service that uses `InternsRepository` with validation and guard checks.
- **[NEW] src/modules/interns/interns.controller.ts** – REST controller exposing CRUD endpoints (`/interns`). Routes protected by `JwtAuthGuard` and `RolesGuard` (Authority role only for create/update/delete, Intern can read their own profile).
- **[NEW] src/modules/interns/interns.module.ts** – Nest module wiring controller, service, repository, and exporting where needed.

---
### Assignments Module
- **[NEW] src/modules/assignments/assignments.controller.ts** – CRUD endpoints (`/assignments`). Create/Update/Delete guarded to Authority role; list endpoints support pagination, filtering, sorting via query DTO.
- **[NEW] src/modules/assignments/assignments.module.ts** – Module declaration importing service, repository, controller.
- **[NEW] src/modules/assignments/dto/query-assignments.dto.ts** – DTO for pagination/filter parameters.

---
### Dashboard Module
- **[NEW] src/modules/dashboard/dashboard.service.ts** – Service aggregating data:
  - Authority view: total interns, active assignments, pending/completed reviews counts.
  - Intern view: assigned tasks, completed tasks, upcoming deadlines.
- **[NEW] src/modules/dashboard/dashboard.controller.ts** – Two GET endpoints:
  - `/dashboard/authority` (Authority role).
  - `/dashboard/intern` (Intern role).
- **[NEW] src/modules/dashboard/dashboard.module.ts** – Module wiring service and controller.

---
### App Module Integration
- **[MODIFY] src/app.module.ts** – Import `InternsModule`, `AssignmentsModule`, `DashboardModule`.
- Ensure `ConfigModule`, `PrismaModule`, `AuthModule`, `UsersModule`, `RolesModule`, `AuthoritiesModule`, `AuditModule` remain imported.

---
### README Update
- **[MODIFY] README.md** – Add sections describing the newly available endpoints, example requests, and authentication/authorization details.

## Verification Plan
### Automated Tests
- Run `npm run test` (existing test suite) to ensure no regressions.
- Execute Prisma generate (`npx prisma generate`) and run a simple seed script to verify DB schema matches new models.
- Use `curl`/`httpie` to hit a few endpoints (e.g., `GET /interns`, `POST /assignments`) with a valid JWT to confirm responses and guards.

### Manual Verification
- Spin up the NestJS dev server (`npm run start:dev`).
- Open Swagger UI (`/api`) and manually test each new route, checking role restrictions.
- Verify dashboard aggregates return sensible numbers based on seeded data.

---
