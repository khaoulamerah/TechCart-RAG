"""
backend/rag/sql_store/database.py

Gestion de la connexion PostgreSQL avec SQLAlchemy async.

CONCEPT : Connection Pooling
─────────────────────────────────────────────────────────
Sans pool : Ouvrir connexion → Requête → Fermer connexion
            (lent, coûteux pour chaque requête)

Avec pool : Maintenir N connexions ouvertes en permanence
            Chaque requête emprunte une connexion → la rend
            (rapide, efficace)

SQLAlchemy gère le pool automatiquement.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import text

from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# ENGINE (Connexion principale)
# ─────────────────────────────────────────────────────────────
def create_engine() -> AsyncEngine:
    """
    Crée le moteur SQLAlchemy async.
    
    L'engine gère le pool de connexions.
    Il est créé UNE SEULE FOIS au démarrage de l'application.
    """
    engine = create_async_engine(
        settings.database_url,
        
        # Pool de connexions
        pool_size=5,
        # pool_size = nombre de connexions maintenues en permanence
        
        max_overflow=10,
        # max_overflow = connexions supplémentaires si pool saturé
        # Donc : max 5+10=15 connexions simultanées
        
        pool_pre_ping=True,
        # pool_pre_ping = vérifie que la connexion est vivante
        # avant de l'utiliser (évite les erreurs après idle)
        
        echo=settings.debug,
        # echo=True en DEBUG = log toutes les requêtes SQL
        # Très utile pour comprendre ce que SQLAlchemy génère
        # Désactiver en production (trop verbeux)
    )
    
    return engine


# ─────────────────────────────────────────────────────────────
# SESSION FACTORY
# ─────────────────────────────────────────────────────────────
# L'engine est créé une fois (variable module-level)
engine = create_engine()

# Session factory : crée des sessions de transaction
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    # expire_on_commit=False : les objets restent utilisables
    # après un commit (sans nécessiter un refresh)
)


# ─────────────────────────────────────────────────────────────
# SESSION DEPENDENCY (pour FastAPI)
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager qui fournit une session de DB.
    
    Usage:
        async with get_session() as session:
            result = await session.execute(select(Product))
    
    Gère automatiquement :
    - Ouverture de la session
    - Commit si tout va bien
    - Rollback si une erreur survient
    - Fermeture de la session dans tous les cas
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Version generator pour FastAPI Depends().
    
    FastAPI injecte automatiquement la session dans
    les routes qui le demandent via Depends(get_db_session).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────
async def check_database_connection() -> bool:
    """Vérifie que la base de données est accessible."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✅ Database connection OK")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False