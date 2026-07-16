"""
Platform Admin Routes - Super Admin Only
Full system administration for self-hosted deployments
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
import json
from ..middleware.auth import get_current_user, get_db

router = APIRouter(prefix="/v1/platform", tags=["platform-admin"])

# ============================================
# Auth Helper - SUPERADMIN ONLY
# ============================================

async def require_superadmin(current_user: Dict = Depends(get_current_user)):
    """Ensure user is superadmin"""
    if current_user.get("role") != "superadmin":
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Super Admin only."
        )
    return current_user

# ============================================
# Models
# ============================================

class CompanyUpdate(BaseModel):
    plan: Optional[str] = None
    monthly_quota: Optional[int] = None
    used_quota: Optional[int] = None
    is_active: Optional[bool] = None

class UserRoleUpdate(BaseModel):
    role: str

class UserStatusUpdate(BaseModel):
    is_active: bool

class PlatformSettings(BaseModel):
    default_llm_provider: Optional[str] = None
    default_llm_model: Optional[str] = None
    max_file_size_mb: Optional[int] = None
    max_queries_per_day_free: Optional[int] = None
    max_contracts_free: Optional[int] = None
    registration_enabled: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    allowed_file_types: Optional[List[str]] = None
    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None
    feature_flags: Optional[Dict] = None

# ============================================
# DASHBOARD
# ============================================

@router.get("/stats")
async def get_platform_stats(admin: Dict = Depends(require_superadmin)):
    """Overall platform statistics"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        stats = {}
        
        # Total companies
        cur.execute("SELECT COUNT(*) as count FROM companies")
        stats["total_companies"] = cur.fetchone()["count"]
        
        # Total users
        cur.execute("SELECT COUNT(*) as count FROM users WHERE is_active = true")
        stats["total_users"] = cur.fetchone()["count"]
        
        # Total documents
        try:
            cur.execute("SELECT COUNT(*) as count FROM documents")
            stats["total_documents"] = cur.fetchone()["count"]
        except:
            stats["total_documents"] = 0
        
        # Total contracts
        try:
            cur.execute("SELECT COUNT(*) as count FROM contracts WHERE status != 'deleted'")
            stats["total_contracts"] = cur.fetchone()["count"]
        except:
            stats["total_contracts"] = 0
        
        # Law database size
        cur.execute("SELECT COUNT(*) as count FROM law_documents")
        stats["total_law_documents"] = cur.fetchone()["count"]
        
        cur.execute("SELECT COUNT(*) as count FROM law_chunks")
        stats["total_law_chunks"] = cur.fetchone()["count"]
        
        # Queries today
        try:
            cur.execute("""
                SELECT COUNT(*) as count FROM usage_logs 
                WHERE created_at >= CURRENT_DATE
            """)
            stats["total_queries_today"] = cur.fetchone()["count"]
        except:
            stats["total_queries_today"] = 0
        
        # Queries this month
        try:
            cur.execute("""
                SELECT COUNT(*) as count FROM usage_logs 
                WHERE created_at >= date_trunc('month', CURRENT_DATE)
            """)
            stats["total_queries_month"] = cur.fetchone()["count"]
        except:
            stats["total_queries_month"] = 0
        
        # Active users today (last 24h)
        cur.execute("""
            SELECT COUNT(DISTINCT user_id) as count FROM usage_logs 
            WHERE created_at >= NOW() - INTERVAL '24 hours' AND user_id IS NOT NULL
        """)
        stats["active_users_today"] = cur.fetchone()["count"] or 0
        
        # Storage used (placeholder)
        stats["storage_used_mb"] = 0
        
        # Companies by plan
        cur.execute("""
            SELECT plan, COUNT(*) as count
            FROM companies
            GROUP BY plan
        """)
        plans = cur.fetchall()
        stats["companies_by_plan"] = {p["plan"]: p["count"] for p in plans}
        
        # Top companies by usage (this month)
        try:
            cur.execute("""
                SELECT c.name, COUNT(*) as queries
                FROM usage_logs ul
                JOIN companies c ON c.id = ul.company_id
                WHERE ul.created_at >= date_trunc('month', CURRENT_DATE)
                GROUP BY c.id, c.name
                ORDER BY queries DESC
                LIMIT 5
            """)
            stats["top_companies"] = [dict(r) for r in cur.fetchall()]
        except:
            stats["top_companies"] = []
        
        # Daily usage (last 30 days)
        try:
            cur.execute("""
                SELECT DATE(created_at) as date, 
                       COUNT(*) as queries,
                       COUNT(DISTINCT user_id) as users
                FROM usage_logs
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """)
            stats["daily_usage"] = [dict(r) for r in cur.fetchall()]
        except:
            stats["daily_usage"] = []
        
        return stats

# ============================================
# COMPANY MANAGEMENT
# ============================================

@router.get("/companies")
async def list_all_companies(
    search: Optional[str] = None,
    plan: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(200, le=500),
    offset: int = 0,
    admin: Dict = Depends(require_superadmin)
):
    """List all companies with stats"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                c.id, c.name, c.slug, c.plan, c.monthly_quota, c.used_quota,
                c.is_active, c.created_at, c.metadata,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(DISTINCT d.id) as document_count,
                COUNT(DISTINCT ct.id) as contract_count
            FROM companies c
            LEFT JOIN users u ON u.company_id = c.id AND u.is_active = true
            LEFT JOIN documents d ON d.company_id = c.id
            LEFT JOIN contracts ct ON ct.company_id = c.id AND ct.status != 'deleted'
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (c.name ILIKE %s OR c.slug ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        if plan:
            query += " AND c.plan = %s"
            params.append(plan)
        
        if status == "active":
            query += " AND c.is_active = true"
        elif status == "inactive":
            query += " AND c.is_active = false"
        
        query += """
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cur.execute(query, params)
        companies = [dict(r) for r in cur.fetchall()]
        
        # Convert UUID and datetime to string
        for c in companies:
            c["id"] = str(c["id"])
            if c.get("created_at"):
                c["created_at"] = c["created_at"].isoformat()
        
        return {"companies": companies, "total": len(companies)}

@router.get("/companies/{company_id}")
async def get_company_detail(company_id: str, admin: Dict = Depends(require_superadmin)):
    """Get detailed company info"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
        company = cur.fetchone()
        if not company:
            raise HTTPException(404, "Company does not exist")
        
        company = dict(company)
        company["id"] = str(company["id"])
        if company.get("created_at"):
            company["created_at"] = company["created_at"].isoformat()
        
        # Members
        cur.execute("""
            SELECT id, email, full_name, role, is_active, last_login_at, created_at
            FROM users
            WHERE company_id = %s
            ORDER BY created_at ASC
        """, (company_id,))
        members = cur.fetchall()
        company["members"] = []
        for m in members:
            member = dict(m)
            member["id"] = str(member["id"])
            if member.get("created_at"):
                member["created_at"] = member["created_at"].isoformat()
            if member.get("last_login_at"):
                member["last_login_at"] = member["last_login_at"].isoformat()
            company["members"].append(member)
        
        # Usage stats (last 30 days)
        try:
            cur.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as queries
                FROM usage_logs
                WHERE company_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (company_id,))
            usage = cur.fetchall()
            company["usage_history"] = [{"date": str(u["date"]), "queries": u["queries"]} for u in usage]
        except:
            company["usage_history"] = []
        
        return company

@router.put("/companies/{company_id}")
async def update_company(
    company_id: str,
    update: CompanyUpdate,
    admin: Dict = Depends(require_superadmin)
):
    """Update company settings"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        updates = []
        params = []
        
        if update.plan is not None:
            updates.append("plan = %s::plan_type")
            params.append(update.plan)
        
        if update.monthly_quota is not None:
            updates.append("monthly_quota = %s")
            params.append(update.monthly_quota)
        
        if update.used_quota is not None:
            updates.append("used_quota = %s")
            params.append(update.used_quota)
        
        if update.is_active is not None:
            updates.append("is_active = %s")
            params.append(update.is_active)
        
        if not updates:
            raise HTTPException(400, "No updates")
        
        query = f"UPDATE companies SET {', '.join(updates)} WHERE id = %s RETURNING *"
        params.append(company_id)
        
        cur.execute(query, params)
        updated = cur.fetchone()
        
        if not updated:
            raise HTTPException(404, "Company does not exist")
        
        conn.commit()
        
        result = dict(updated)
        result["id"] = str(result["id"])
        if result.get("created_at"):
            result["created_at"] = result["created_at"].isoformat()
        
        # Log to platform_logs
        try:
            cur.execute("""
                INSERT INTO platform_logs (user_id, action, target_type, target_id, details)
                VALUES (%s, 'update_company', 'company', %s, %s)
            """, (admin["id"], company_id, json.dumps(update.dict(exclude_none=True))))
            conn.commit()
        except:
            pass
        
        return result

@router.get("/companies/{company_id}/users")
async def get_company_users(company_id: str, admin: Dict = Depends(require_superadmin)):
    """Get all users of a company"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, email, full_name, role, is_active, last_login_at, created_at
            FROM users
            WHERE company_id = %s
            ORDER BY created_at ASC
        """, (company_id,))
        users = cur.fetchall()
        
        result = []
        for u in users:
            user = dict(u)
            user["id"] = str(user["id"])
            if user.get("created_at"):
                user["created_at"] = user["created_at"].isoformat()
            if user.get("last_login_at"):
                user["last_login_at"] = user["last_login_at"].isoformat()
            result.append(user)
        
        return {"users": result}

# ============================================
# USER MANAGEMENT
# ============================================

@router.get("/users")
async def list_all_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(200, le=1000),
    offset: int = 0,
    admin: Dict = Depends(require_superadmin)
):
    """List all users across all companies"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                u.id, u.email, u.full_name, u.role, u.company_id, u.is_active,
                u.last_login_at, u.created_at,
                c.name as company_name, c.plan as company_plan
            FROM users u
            LEFT JOIN companies c ON c.id = u.company_id
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (u.email ILIKE %s OR u.full_name ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        if role:
            query += " AND u.role = %s"
            params.append(role)
        
        if company_id:
            query += " AND u.company_id = %s"
            params.append(company_id)
        
        if status == "active":
            query += " AND u.is_active = true"
        elif status == "inactive":
            query += " AND u.is_active = false"
        
        query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        users = cur.fetchall()
        
        result = []
        for u in users:
            user = dict(u)
            user["id"] = str(user["id"])
            if user.get("company_id"):
                user["company_id"] = str(user["company_id"])
            if user.get("created_at"):
                user["created_at"] = user["created_at"].isoformat()
            if user.get("last_login_at"):
                user["last_login_at"] = user["last_login_at"].isoformat()
            result.append(user)
        
        return {"users": result}

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    update: UserRoleUpdate,
    admin: Dict = Depends(require_superadmin)
):
    """Change user role"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            UPDATE users SET role = %s::user_role WHERE id = %s RETURNING *
        """, (update.role, user_id))
        
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(404, "User does not exist")
        
        conn.commit()
        
        result = dict(updated)
        result["id"] = str(result["id"])
        
        return result

@router.put("/users/{user_id}/status")
async def change_user_status(
    user_id: str,
    update: UserStatusUpdate,
    admin: Dict = Depends(require_superadmin)
):
    """Activate/deactivate user"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            UPDATE users SET is_active = %s WHERE id = %s RETURNING *
        """, (update.is_active, user_id))
        
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(404, "User does not exist")
        
        conn.commit()
        
        result = dict(updated)
        result["id"] = str(result["id"])
        
        return result

# ============================================
# SYSTEM SETTINGS
# ============================================

@router.get("/settings")
async def get_platform_settings(admin: Dict = Depends(require_superadmin)):
    """Get all platform settings"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT key, value FROM platform_settings")
        rows = cur.fetchall()
        
        settings = {}
        for row in rows:
            settings[row["key"]] = row["value"]
        
        # Merge all settings into one object
        result = {
            "default_llm_provider": settings.get("llm", {}).get("default_provider", "groq"),
            "default_llm_model": settings.get("llm", {}).get("default_model", "groq-llama"),
            "max_file_size_mb": settings.get("limits", {}).get("max_file_size_mb", 50),
            "max_queries_per_day_free": settings.get("limits", {}).get("max_queries_per_day_free", 10),
            "max_contracts_free": settings.get("limits", {}).get("max_contracts_free", 1),
            "registration_enabled": settings.get("general", {}).get("registration_enabled", True),
            "require_email_verification": settings.get("general", {}).get("require_email_verification", False),
            "allowed_file_types": settings.get("limits", {}).get("allowed_file_types", [".pdf", ".doc", ".docx", ".txt"]),
            "maintenance_mode": settings.get("general", {}).get("maintenance_mode", False),
            "maintenance_message": settings.get("general", {}).get("maintenance_message", ""),
            "feature_flags": settings.get("features", {})
        }
        
        return result

@router.put("/settings")
async def update_platform_settings(
    settings: PlatformSettings,
    admin: Dict = Depends(require_superadmin)
):
    """Update platform settings"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Update general settings
        if settings.registration_enabled is not None or settings.require_email_verification is not None or settings.maintenance_mode is not None:
            cur.execute("SELECT value FROM platform_settings WHERE key = 'general'")
            row = cur.fetchone()
            general = row["value"] if row else {}
            
            if settings.registration_enabled is not None:
                general["registration_enabled"] = settings.registration_enabled
            if settings.require_email_verification is not None:
                general["require_email_verification"] = settings.require_email_verification
            if settings.maintenance_mode is not None:
                general["maintenance_mode"] = settings.maintenance_mode
            if settings.maintenance_message is not None:
                general["maintenance_message"] = settings.maintenance_message
            
            cur.execute("""
                INSERT INTO platform_settings (key, value, updated_by)
                VALUES ('general', %s, %s)
                ON CONFLICT (key) DO UPDATE SET value = %s, updated_by = %s, updated_at = NOW()
            """, (json.dumps(general), admin["id"], json.dumps(general), admin["id"]))
        
        # Update limits
        if any([settings.max_file_size_mb, settings.max_queries_per_day_free, settings.max_contracts_free, settings.allowed_file_types]):
            cur.execute("SELECT value FROM platform_settings WHERE key = 'limits'")
            row = cur.fetchone()
            limits = row["value"] if row else {}
            
            if settings.max_file_size_mb is not None:
                limits["max_file_size_mb"] = settings.max_file_size_mb
            if settings.max_queries_per_day_free is not None:
                limits["max_queries_per_day_free"] = settings.max_queries_per_day_free
            if settings.max_contracts_free is not None:
                limits["max_contracts_free"] = settings.max_contracts_free
            if settings.allowed_file_types is not None:
                limits["allowed_file_types"] = settings.allowed_file_types
            
            cur.execute("""
                INSERT INTO platform_settings (key, value, updated_by)
                VALUES ('limits', %s, %s)
                ON CONFLICT (key) DO UPDATE SET value = %s, updated_by = %s, updated_at = NOW()
            """, (json.dumps(limits), admin["id"], json.dumps(limits), admin["id"]))
        
        # Update LLM settings
        if settings.default_llm_provider or settings.default_llm_model:
            cur.execute("SELECT value FROM platform_settings WHERE key = 'llm'")
            row = cur.fetchone()
            llm = row["value"] if row else {}
            
            if settings.default_llm_provider:
                llm["default_provider"] = settings.default_llm_provider
            if settings.default_llm_model:
                llm["default_model"] = settings.default_llm_model
            
            cur.execute("""
                INSERT INTO platform_settings (key, value, updated_by)
                VALUES ('llm', %s, %s)
                ON CONFLICT (key) DO UPDATE SET value = %s, updated_by = %s, updated_at = NOW()
            """, (json.dumps(llm), admin["id"], json.dumps(llm), admin["id"]))
        
        # Update feature flags
        if settings.feature_flags:
            cur.execute("""
                INSERT INTO platform_settings (key, value, updated_by)
                VALUES ('features', %s, %s)
                ON CONFLICT (key) DO UPDATE SET value = %s, updated_by = %s, updated_at = NOW()
            """, (json.dumps(settings.feature_flags), admin["id"], json.dumps(settings.feature_flags), admin["id"]))
        
        conn.commit()
        
        return {"message": "Settings updated successfully", "updated_by": admin["email"]}

# ============================================
# AUDIT LOGS
# ============================================

@router.get("/logs")
async def get_platform_logs(
    action: Optional[str] = None,
    limit: int = Query(100, le=1000),
    admin: Dict = Depends(require_superadmin)
):
    """Get platform audit logs"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT pl.*, u.email as user_email, u.full_name as user_name
            FROM platform_logs pl
            LEFT JOIN users u ON u.id = pl.user_id
            WHERE 1=1
        """
        params = []
        
        if action:
            query += " AND pl.action = %s"
            params.append(action)
        
        query += " ORDER BY pl.created_at DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        logs = cur.fetchall()
        
        result = []
        for log in logs:
            l = dict(log)
            if l.get("id"):
                l["id"] = str(l["id"])
            if l.get("user_id"):
                l["user_id"] = str(l["user_id"])
            if l.get("created_at"):
                l["created_at"] = l["created_at"].isoformat()
            result.append(l)
        
        return {"logs": result}

# ============================================
# LLM USAGE & COST
# ============================================

@router.get("/llm-usage")
async def get_llm_usage(admin: Dict = Depends(require_superadmin)):
    """LLM usage stats and cost estimation"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total tokens today
        try:
            cur.execute("""
                SELECT SUM(input_tokens) as input, SUM(output_tokens) as output
                FROM llm_usage
                WHERE created_at >= CURRENT_DATE
            """)
            today = cur.fetchone()
        except:
            today = {"input": 0, "output": 0}
        
        # Total tokens this month
        try:
            cur.execute("""
                SELECT SUM(input_tokens) as input, SUM(output_tokens) as output
                FROM llm_usage
                WHERE created_at >= date_trunc('month', CURRENT_DATE)
            """)
            month = cur.fetchone()
        except:
            month = {"input": 0, "output": 0}
        
        # By provider
        try:
            cur.execute("""
                SELECT provider, SUM(input_tokens + output_tokens) as tokens
                FROM llm_usage
                WHERE created_at >= date_trunc('month', CURRENT_DATE)
                GROUP BY provider
            """)
            by_provider = {r["provider"]: r["tokens"] for r in cur.fetchall()}
        except:
            by_provider = {}
        
        # By company (top 10)
        try:
            cur.execute("""
                SELECT c.name, SUM(lu.input_tokens + lu.output_tokens) as tokens
                FROM llm_usage lu
                JOIN companies c ON c.id = lu.company_id
                WHERE lu.created_at >= date_trunc('month', CURRENT_DATE)
                GROUP BY c.id, c.name
                ORDER BY tokens DESC
                LIMIT 10
            """)
            by_company = [dict(r) for r in cur.fetchall()]
        except:
            by_company = []
        
        total_tokens_month = (month.get("input") or 0) + (month.get("output") or 0)
        
        # Simple cost estimation (Groq Llama 3.3 70B: $0.59 per 1M input, $0.79 per 1M output)
        estimated_cost = ((month.get("input") or 0) / 1_000_000 * 0.59) + ((month.get("output") or 0) / 1_000_000 * 0.79)
        
        return {
            "total_tokens_today": (today.get("input") or 0) + (today.get("output") or 0),
            "total_tokens_month": total_tokens_month,
            "estimated_cost_month_usd": round(estimated_cost, 2),
            "by_provider": by_provider,
            "by_company": by_company
        }

# ============================================
# MAINTENANCE
# ============================================

@router.get("/maintenance/db-stats")
async def get_db_stats(admin: Dict = Depends(require_superadmin)):
    """Database statistics"""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        stats = {}
        
        tables = ["companies", "users", "documents", "contracts", "law_documents", "law_chunks", "usage_logs"]
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = cur.fetchone()["count"]
            except:
                stats[table] = 0
        
        # Database size (PostgreSQL)
        try:
            cur.execute("SELECT pg_database_size(current_database()) as size")
            size_bytes = cur.fetchone()["size"]
            stats["database_size_mb"] = round(size_bytes / 1024 / 1024, 2)
        except:
            stats["database_size_mb"] = 0
        
        return stats

@router.post("/maintenance/cleanup")
async def cleanup_deleted(admin: Dict = Depends(require_superadmin)):
    """Clean up soft-deleted documents older than 30 days"""
    with get_db() as conn:
        cur = conn.cursor()
        
        try:
            cur.execute("""
                DELETE FROM contracts
                WHERE status = 'deleted' AND updated_at < NOW() - INTERVAL '30 days'
            """)
            deleted = cur.rowcount
            conn.commit()
            
            return {"cleaned": deleted, "message": f"Deleted {deleted} contract(s)"}
        except Exception as e:
            return {"error": str(e)}
