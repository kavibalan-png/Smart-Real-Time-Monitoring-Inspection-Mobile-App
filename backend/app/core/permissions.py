"""
Role-Based Access Control definitions.
All permissions are enforced server-side — never trust frontend roles.
"""
from enum import Enum
from typing import Set


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    DEPARTMENT_OFFICIAL = "DEPARTMENT_OFFICIAL"
    PMU_OFFICER = "PMU_OFFICER"
    INSPECTION_OFFICER = "INSPECTION_OFFICER"
    PROJECT_ADMIN = "PROJECT_ADMIN"
    PROJECT_STAFF = "PROJECT_STAFF"
    CITIZEN = "CITIZEN"


class Permission(str, Enum):
    # Project management
    PROJECT_READ_ALL = "project:read:all"
    PROJECT_READ_OWN = "project:read:own"
    PROJECT_WRITE = "project:write"

    # Monitoring & analytics
    MONITORING_READ = "monitoring:read"
    ANALYTICS_READ = "analytics:read"
    ANOMALY_READ = "anomaly:read"

    # Inspection
    INSPECTION_ASSIGN = "inspection:assign"
    INSPECTION_READ_ALL = "inspection:read:all"
    INSPECTION_READ_OWN = "inspection:read:own"
    INSPECTION_CONDUCT = "inspection:conduct"
    INSPECTION_REVIEW = "inspection:review"

    # Evidence
    EVIDENCE_UPLOAD = "evidence:upload"
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_VERIFY = "evidence:verify"

    # CCTV
    CCTV_READ = "cctv:read"

    # Official decisions
    DECISION_MAKE = "decision:make"

    # Follow-up
    FOLLOWUP_READ = "followup:read"
    FOLLOWUP_WRITE = "followup:write"

    # Audit
    AUDIT_READ = "audit:read"

    # Notifications
    NOTIFICATION_READ = "notification:read"

    # Admin
    USER_MANAGE = "user:manage"


# Role → permissions mapping (least privilege principle)
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.SUPER_ADMIN: set(Permission),  # All permissions

    UserRole.DEPARTMENT_OFFICIAL: {
        Permission.PROJECT_READ_ALL,
        Permission.MONITORING_READ,
        Permission.ANALYTICS_READ,
        Permission.ANOMALY_READ,
        Permission.INSPECTION_ASSIGN,
        Permission.INSPECTION_READ_ALL,
        Permission.INSPECTION_REVIEW,
        Permission.EVIDENCE_READ,
        Permission.EVIDENCE_VERIFY,
        Permission.CCTV_READ,
        Permission.DECISION_MAKE,
        Permission.FOLLOWUP_READ,
        Permission.FOLLOWUP_WRITE,
        Permission.AUDIT_READ,
        Permission.NOTIFICATION_READ,
    },

    UserRole.PMU_OFFICER: {
        Permission.PROJECT_READ_ALL,
        Permission.MONITORING_READ,
        Permission.ANALYTICS_READ,
        Permission.ANOMALY_READ,
        Permission.INSPECTION_ASSIGN,
        Permission.INSPECTION_READ_ALL,
        Permission.INSPECTION_REVIEW,
        Permission.EVIDENCE_READ,
        Permission.EVIDENCE_VERIFY,
        Permission.CCTV_READ,
        Permission.FOLLOWUP_READ,
        Permission.FOLLOWUP_WRITE,
        Permission.NOTIFICATION_READ,
        Permission.AUDIT_READ,
    },

    UserRole.INSPECTION_OFFICER: {
        Permission.INSPECTION_READ_OWN,
        Permission.INSPECTION_CONDUCT,
        Permission.EVIDENCE_UPLOAD,
        Permission.EVIDENCE_READ,
        Permission.PROJECT_READ_OWN,
        Permission.NOTIFICATION_READ,
        Permission.FOLLOWUP_READ,
    },

    UserRole.PROJECT_ADMIN: {
        Permission.PROJECT_READ_OWN,
        Permission.PROJECT_WRITE,
        Permission.FOLLOWUP_READ,
        Permission.FOLLOWUP_WRITE,
        Permission.NOTIFICATION_READ,
    },

    UserRole.PROJECT_STAFF: {
        Permission.PROJECT_READ_OWN,
        Permission.FOLLOWUP_READ,
        Permission.NOTIFICATION_READ,
    },

    UserRole.CITIZEN: {
        Permission.NOTIFICATION_READ,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return permission in role_perms


def get_permissions(role: UserRole) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())
