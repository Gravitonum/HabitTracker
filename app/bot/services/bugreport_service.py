"""
Сервис для работы с отчетами об ошибках.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_, or_
from app.models.database import BugReport, User
from app.models.schemas import BugReportCreate, BugReportUpdate
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def create_bug_report(db: Session, bug_report: BugReportCreate) -> BugReport:
    """
    Создать новый отчет об ошибке.
    """
    try:
        db_bug_report = BugReport(
            user_id=bug_report.user_id,
            title=bug_report.title,
            description=bug_report.description,
            incident_type=bug_report.incident_type,
            status=bug_report.status,
            admin_comment=bug_report.admin_comment,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_bug_report)
        db.commit()
        db.refresh(db_bug_report)
        
        logger.info(f"Создан отчет об ошибке {db_bug_report.id} от пользователя {bug_report.user_id}")
        return db_bug_report
        
    except Exception as e:
        logger.error(f"Ошибка при создании отчета об ошибке: {e}")
        db.rollback()
        raise


def get_bug_report_by_id(db: Session, bug_report_id: str) -> Optional[BugReport]:
    """
    Получить отчет об ошибке по ID.
    """
    try:
        from uuid import UUID
        # Преобразуем строку в UUID
        uuid_id = UUID(bug_report_id)
        result = db.execute(select(BugReport).where(BugReport.id == uuid_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Ошибка при получении отчета об ошибке {bug_report_id}: {e}")
        return None


def get_all_bug_reports(db: Session, skip: int = 0, limit: int = 100) -> List[BugReport]:
    """
    Получить все отчеты об ошибках с пагинацией.
    """
    try:
        result = db.execute(
            select(BugReport)
            .order_by(desc(BugReport.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка при получении всех отчетов об ошибках: {e}")
        return []


def get_bug_reports_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[BugReport]:
    """
    Получить отчеты об ошибках по статусу.
    """
    try:
        result = db.execute(
            select(BugReport)
            .where(BugReport.status == status)
            .order_by(desc(BugReport.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка при получении отчетов об ошибках по статусу {status}: {e}")
        return []


def get_bug_reports_by_incident_type(db: Session, incident_type: str, skip: int = 0, limit: int = 100) -> List[BugReport]:
    """
    Получить отчеты об ошибках по типу инцидента.
    """
    try:
        result = db.execute(
            select(BugReport)
            .where(BugReport.incident_type == incident_type)
            .order_by(desc(BugReport.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка при получении отчетов об ошибках по типу {incident_type}: {e}")
        return []


def get_bug_reports_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[BugReport]:
    """
    Получить отчеты об ошибках по пользователю.
    """
    try:
        result = db.execute(
            select(BugReport)
            .where(BugReport.user_id == user_id)
            .order_by(desc(BugReport.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка при получении отчетов об ошибках пользователя {user_id}: {e}")
        return []


def update_bug_report(db: Session, bug_report_id: str, bug_report_update: BugReportUpdate) -> Optional[BugReport]:
    """
    Обновить отчет об ошибке.
    """
    try:
        from uuid import UUID
        uuid_id = UUID(bug_report_id)
        
        # Получаем отчет напрямую
        result = db.execute(select(BugReport).where(BugReport.id == uuid_id))
        db_bug_report = result.scalar_one_or_none()
        
        if not db_bug_report:
            return None
            
        update_data = bug_report_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_bug_report, field, value)
            
        db_bug_report.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_bug_report)
        
        logger.info(f"Обновлен отчет об ошибке {bug_report_id}")
        return db_bug_report
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении отчета об ошибке {bug_report_id}: {e}")
        db.rollback()
        return None


def delete_bug_report(db: Session, bug_report_id: str) -> bool:
    """
    Удалить отчет об ошибке.
    """
    try:
        from uuid import UUID
        uuid_id = UUID(bug_report_id)
        
        # Получаем отчет напрямую
        result = db.execute(select(BugReport).where(BugReport.id == uuid_id))
        db_bug_report = result.scalar_one_or_none()
        
        if not db_bug_report:
            return False
            
        db.delete(db_bug_report)
        db.commit()
        
        logger.info(f"Удален отчет об ошибке {bug_report_id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при удалении отчета об ошибке {bug_report_id}: {e}")
        db.rollback()
        return False


def search_bug_reports(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[BugReport]:
    """
    Поиск отчетов об ошибках по тексту.
    """
    try:
        search_filter = or_(
            BugReport.title.ilike(f"%{query}%"),
            BugReport.description.ilike(f"%{query}%"),
            BugReport.admin_comment.ilike(f"%{query}%")
        )
        
        result = db.execute(
            select(BugReport)
            .where(search_filter)
            .order_by(desc(BugReport.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка при поиске отчетов об ошибках: {e}")
        return []


def get_bug_reports_with_filters(
    db: Session, 
    status: Optional[str] = None,
    incident_type: Optional[str] = None,
    user_id: Optional[str] = None,
    search_query: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[BugReport]:
    """
    Получить отчеты об ошибках с фильтрами.
    """
    try:
        query = select(BugReport)
        
        # Применяем фильтры
        filters = []
        if status:
            filters.append(BugReport.status == status)
        if incident_type:
            filters.append(BugReport.incident_type == incident_type)
        if user_id:
            filters.append(BugReport.user_id == user_id)
        if search_query:
            search_filter = or_(
                BugReport.title.ilike(f"%{search_query}%"),
                BugReport.description.ilike(f"%{search_query}%"),
                BugReport.admin_comment.ilike(f"%{search_query}%")
            )
            filters.append(search_filter)
            
        if filters:
            query = query.where(and_(*filters))
            
        result = db.execute(
            query
            .order_by(desc(BugReport.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка при получении отчетов об ошибках с фильтрами: {e}")
        return []


def get_bug_report_statistics(db: Session) -> dict:
    """
    Получить статистику по отчетам об ошибках.
    """
    try:
        total_reports = db.execute(select(BugReport)).scalars().all()
        
        stats = {
            "total": len(total_reports),
            "by_status": {},
            "by_incident_type": {},
            "recent_24h": 0
        }
        
        # Статистика по статусам
        for report in total_reports:
            status = report.status
            if status not in stats["by_status"]:
                stats["by_status"][status] = 0
            stats["by_status"][status] += 1
            
            # Статистика по типам инцидентов
            incident_type = report.incident_type
            if incident_type not in stats["by_incident_type"]:
                stats["by_incident_type"][incident_type] = 0
            stats["by_incident_type"][incident_type] += 1
            
            # Отчеты за последние 24 часа
            if report.created_at and (datetime.utcnow() - report.created_at).days < 1:
                stats["recent_24h"] += 1
                
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики отчетов об ошибках: {e}")
        return {"total": 0, "by_status": {}, "by_incident_type": {}, "recent_24h": 0}
