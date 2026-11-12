# Commit Conventions

## 1. Purpose

This document defines the commit message format and conventions used across the project.

Consistent commit messages improve readability, simplify code history analysis, and enable automation such as changelog generation, semantic versioning, and release management.

The project follows the Conventional Commits specification with additional conventions for microservices and infrastructure components.

## 2. Commit Message Format

All commit messages should follow this format:

```text
<type>(<scope>): <description>
```

Where:

- `type` describes the nature of the change.
- `scope` identifies the affected component or project area.
- `description` briefly explains the change.

Example:

```text
feat(auth-service): add JWT authentication
```

The scope is recommended for all commits. If a change genuinely affects the entire project and has no meaningful narrower scope, it may be omitted.

Example:

```text
docs: update project documentation
```

## 3. Commit Types

The following commit types are used in the project.

| Type | Description |
|---|---|
| `feat` | Introduces a new feature or functionality. |
| `fix` | Fixes a bug or incorrect behavior. |
| `refactor` | Changes internal implementation without changing external behavior. |
| `perf` | Improves performance. |
| `test` | Adds or modifies tests. |
| `docs` | Adds or updates documentation. |
| `style` | Changes formatting or code style without affecting functionality. |
| `build` | Changes build processes, Docker images, or build-related dependencies. |
| `ci` | Changes CI/CD pipelines and automation. |
| `chore` | Performs maintenance tasks that do not directly change application functionality. |
| `revert` | Reverts a previous commit. |

### 3.1. Type Selection Guidelines

Use `feat` when introducing new functionality.

```text
feat(auth-service): add OAuth2 authentication
```

Use `fix` when correcting existing behavior.

```text
fix(user-service): handle invalid email addresses
```

Use `refactor` when restructuring code without changing its behavior.

```text
refactor(payment-service): simplify payment processing
```

Use `perf` when improving performance.

```text
perf(api-gateway): optimize request routing
```

Use `test` when adding or modifying tests.

```text
test(auth-service): add authentication integration tests
```

Use `docs` when updating documentation.

```text
docs(architecture): add service dependency diagram
```

Use `build` for Dockerfiles, container images, build configurations, and build dependencies.

```text
build(docker): use GHCR images across microservices
```

Use `ci` for CI/CD workflows and automation.

```text
ci(github): add automated deployment workflow
```

Use `chore` for general maintenance tasks.

```text
chore(deps): update development dependencies
```

## 4. Commit Scopes

The scope identifies the component affected by a change.

Scopes should be based on the project's architecture and directory structure.

The following scopes are recommended examples.

### 4.1. Microservices

| Scope | Description |
|---|---|
| `auth-service` | Authentication and authorization service. |
| `user-service` | User management service. |
| `payment-service` | Payment processing service. |
| `notification-service` | Notification service. |
| `api-gateway` | API Gateway and request routing. |

### 4.2. Infrastructure

| Scope | Description |
|---|---|
| `k8s` | Kubernetes manifests, Helm charts, and cluster configuration. |
| `docker` | Dockerfiles, Docker Compose, container configuration. |
| `grafana` | Grafana dashboards and configuration. |
| `prometheus` | Prometheus metrics and configuration. |
| `logging` | Logging infrastructure. |
| `monitoring` | Shared monitoring configuration. |
| `infra` | General infrastructure changes. |

### 4.3. Project-Level Components

| Scope | Description |
|---|---|
| `evaluation` | Evaluation tools, metrics, and benchmarks. |
| `config` | Shared configuration. |
| `deps` | Project dependencies. |
| `github` | GitHub repository configuration and workflows. |
| `architecture` | Architecture documentation and diagrams. |

### 4.4. Scope Guidelines

- Prefer existing scopes whenever possible.
- Use the most specific meaningful scope.
- Use service names for service-specific changes.
- Use infrastructure scopes for shared infrastructure changes.
- Use `infra` only when no more specific infrastructure scope applies.
- Do not create scopes based solely on file extensions.
- New scopes may be introduced when new project components appear.

A scope does not have to match a single directory. It should identify the logical component affected by the change.

## 5. Changes Affecting Multiple Components

When one logical change affects multiple microservices or infrastructure components, use a single commit with a shared scope.

Example:

```text
build(docker): use GHCR images across microservices
```

This is appropriate when the same infrastructure change is applied consistently across several Dockerfiles.

Avoid creating separate commits for every affected service when the changes belong to the same logical task.

However, independent changes should be committed separately.

## 6. Commit Description Guidelines

Commit descriptions should:

- Be written in English.
- Start with a lowercase verb where practical.
- Be concise and descriptive.
- Explain what the change does.
- Avoid unnecessary details.
- Not end with a period.

Examples:

Good:

```text
feat(auth-service): add JWT authentication
fix(payment-service): handle transaction timeout
build(docker): optimize container image layers
```

Bad:

```text
update stuff
fix bug
changes
Docker updates.
```

## 7. Commit Body

A commit may contain an additional body when more context is necessary.

Example:

```text
build(docker): use GHCR images across microservices

- Replace local base images with GHCR images
- Update image references in service Dockerfiles
- Align image tags across services
```

The body should explain the motivation or important implementation details rather than repeat the description.

## 8. Breaking Changes

Changes that introduce backward-incompatible behavior must be explicitly marked.

Use `!` after the type and scope:

```text
feat(api-gateway)!: change authentication API contract
```

Alternatively, use a footer:

```text
feat(api-gateway): change authentication API contract

BREAKING CHANGE: Clients must now provide a Bearer token.
```

Breaking changes may trigger a major version increment when using semantic versioning.

## 9. Reverting Commits

When reverting an earlier commit, use the `revert` type.

Example:

```text
revert(auth-service): revert JWT authentication changes
```

When following the Conventional Commits specification, include the reverted commit reference where appropriate.

## 10. Commit Examples

### Features

```text
feat(auth-service): add JWT authentication
feat(user-service): add user profile endpoint
feat(api-gateway): add request rate limiting
```

### Bug Fixes

```text
fix(auth-service): handle expired refresh tokens
fix(payment-service): resolve transaction timeout
```

### Infrastructure

```text
build(docker): use GHCR images across microservices
chore(grafana): update monitoring dashboards
ci(github): add automated deployment workflow
```

### Testing and Evaluation

```text
test(auth-service): add integration tests
test(evaluation): add regression benchmarks
feat(evaluation): add model performance metrics
```

### Documentation

```text
docs(architecture): document service dependencies
docs(development): add Git workflow guidelines
```

## 11. Commit Validation

Commit messages should be validated automatically using Commitlint or an equivalent tool.

Invalid commit messages should be rejected by the configured validation process.

## 12. Updating These Conventions

The list of commit types and scopes may evolve as the project grows.

New scopes may be introduced when new services or infrastructure components are added.

Changes to these conventions must be submitted through a Pull Request and reviewed by the team.

All developers should follow the latest approved conventions.