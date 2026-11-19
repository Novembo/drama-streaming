---
name: fastapi-development
description: "Build or modify FastAPI applications, routers, dependencies, schemas, middleware, and OpenAPI behavior. Use when working on FastAPI: routers, dependencies, Pydantic schemas, middleware, async endpoints, OpenAPI."
---

# FastAPI Development

## Workflow
1. Inspect app creation, router registration, dependency patterns, settings, lifespan, and test setup.
2. Place endpoints in focused routers; keep HTTP concerns separate from domain/business logic.
3. Define Pydantic request/response schemas explicitly. Do not expose ORM objects or internal fields accidentally.
4. Use dependency injection for authentication, database sessions, and shared services.
5. Choose correct HTTP methods, status codes, response models, and error semantics.
6. Add async only when the full call path uses non-blocking I/O; do not call blocking libraries directly from async endpoints.
7. Add tests for success, validation errors, authorization failures, and relevant edge cases.
8. Check generated OpenAPI behavior and document non-obvious contracts.

## Rules
- Use lifespan context managers for startup/shutdown resources when appropriate.
- Keep configuration in validated settings; do not hardcode credentials.
- Scope database sessions to requests/tasks and close them reliably.
- Avoid putting business logic in route handlers.
- Use explicit response models and avoid leaking stack traces.
- Apply pagination and bounded limits to collection endpoints.
- Set timeouts for outbound HTTP calls and define safe retry/idempotency behavior.
- Do not claim an endpoint is secure merely because it requires a logged-in user.

## Verification
Run the project's tests and configured lint/type checks. If unavailable, state the missing tool or dependency and provide exact commands.

## Examples
```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # explicit response schema, no ORM leak
    id: int
    name: str

@router.get("", response_model=list[ProjectOut])
async def list_projects(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,      # bounded pagination
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = select(Project).where(Project.org_id == user.org_id).order_by(Project.id).limit(limit).offset(offset)
    return (await session.scalars(stmt)).all()

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, session: Annotated[AsyncSession, Depends(get_session)],
                      user: Annotated[User, Depends(current_user)]):
    project = await session.scalar(select(Project).where(Project.id == project_id, Project.org_id == user.org_id))
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")   # object-level scoping
    return project
```

## Related

Language-neutral design vs implementation, or adjacent scope: `fastapi-production-engineering`, `pydantic-v2-patterns`. Load the one that matches the task; load several only when the work spans them.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
