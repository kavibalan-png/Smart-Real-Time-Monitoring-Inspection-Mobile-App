"""
Project management endpoints.
GET  /api/projects          — list with pagination/filters
GET  /api/projects/{id}     — project detail
POST /api/projects          — create project
PUT  /api/projects/{id}     — update project
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.core.permissions import Permission
from app.models.project import Project
from app.models.organization import Organization
from app.schemas.project import ProjectListItem, ProjectDetail, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=dict)
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    district: Optional[str] = None,
    state: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    scheme: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(require_permission(Permission.PROJECT_READ_ALL)),
    db: AsyncSession = Depends(get_db),
):
    """List all projects with pagination and filtering."""
    filters = []
    if district:
        filters.append(Project.district == district)
    if state:
        filters.append(Project.state == state)
    if risk_level:
        filters.append(Project.risk_level == risk_level)
    if status:
        filters.append(Project.status == status)
    if scheme:
        filters.append(Project.scheme == scheme)
    if search:
        filters.append(Project.project_name.ilike(f"%{search}%"))

    count_q = select(func.count(Project.id))
    if filters:
        count_q = count_q.where(and_(*filters))
    total_result = await db.execute(count_q)
    total = total_result.scalar()

    q = select(Project)
    if filters:
        q = q.where(and_(*filters))
    q = q.order_by(Project.risk_level.desc(), Project.health_index.asc())
    q = q.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(q)
    projects = result.scalars().all()

    return {
        "items": [ProjectListItem.model_validate(p) for p in projects],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/hero", response_model=ProjectDetail)
async def get_hero_project(
    current_user=Depends(require_permission(Permission.PROJECT_READ_ALL)),
    db: AsyncSession = Depends(get_db),
):
    """Get the hero demo project (ABC Community Welfare Centre)."""
    result = await db.execute(
        select(Project).where(Project.is_hero_project == True).limit(1)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Hero project not found")
    return project


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project detail. Enforces ownership for PROJECT_STAFF."""
    from app.core.permissions import UserRole, has_permission
    role = UserRole(current_user.role)

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Object-level authorization — staff can only see their org's projects
    if not has_permission(role, Permission.PROJECT_READ_ALL):
        if current_user.organization_id != project.organization_id:
            raise HTTPException(status_code=403, detail="Access denied to this project")

    return project


@router.post("", response_model=ProjectDetail, status_code=201)
async def create_project(
    body: ProjectCreate,
    current_user=Depends(require_permission(Permission.PROJECT_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    import secrets
    from app.core.permissions import UserRole, has_permission
    role = UserRole(current_user.role)
    
    # Enforce organization ownership if not an admin
    org_id = body.organization_id
    if not has_permission(role, Permission.PROJECT_READ_ALL):
        org_id = current_user.organization_id

    code = f"PROJ-{secrets.token_hex(4).upper()}"
    project = Project(
        project_code=code,
        project_name=body.project_name,
        organization_id=org_id,
        scheme=body.scheme,
        district=body.district,
        state=body.state,
        address=body.address,
        latitude=body.latitude,
        longitude=body.longitude,
        beneficiary_count=body.beneficiary_count,
        staff_count=body.staff_count,
        project_type=body.project_type,
        is_demo=True,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    current_user=Depends(require_permission(Permission.PROJECT_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Update project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.core.permissions import UserRole, has_permission
    role = UserRole(current_user.role)
    if not has_permission(role, Permission.PROJECT_READ_ALL):
        if current_user.organization_id != project.organization_id:
            raise HTTPException(status_code=403, detail="Access denied to modify this project")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project
