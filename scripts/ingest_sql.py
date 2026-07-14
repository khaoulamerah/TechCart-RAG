"""
scripts/ingest_sql.py

Charge les données CSV (GPUs + CPUs) dans PostgreSQL.

Usage:
    python scripts/ingest_sql.py
"""

import asyncio
import re
import sys
from pathlib import Path
import pandas as pd

# Ajouter le projet au Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.sql_store.database import AsyncSessionLocal, engine
from backend.rag.sql_store.models import Base, Brand, Category, Product
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def clean_numeric(value) -> float | None:
    """
    Convertit une valeur en float.
    Gère les cas : "2310 MHz", "$599.99", "N/A", NaN
    """
    if pd.isna(value) or str(value).strip() in ('', 'N/A', 'Unknown', 'None'):
        return None
    
    # Supprimer tout sauf chiffres, point, virgule, signe moins
    cleaned = re.sub(r'[^\d.,\-]', '', str(value))
    cleaned = cleaned.replace(',', '.')
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def clean_int(value) -> int | None:
    """Convertit une valeur en int."""
    result = clean_numeric(value)
    return int(result) if result is not None else None


def clean_str(value) -> str | None:
    """Nettoie une chaîne de caractères."""
    if pd.isna(value) or str(value).strip() in ('', 'N/A', 'Unknown', 'None'):
        return None
    return str(value).strip()


async def get_or_create_brand(session: AsyncSession, name: str) -> Brand:
    """Trouve une marque existante ou en crée une nouvelle."""
    slug = name.lower().replace(' ', '-').replace('/', '-')
    
    result = await session.execute(
        select(Brand).where(Brand.slug == slug)
    )
    brand = result.scalar_one_or_none()
    
    if not brand:
        brand = Brand(name=name, slug=slug)
        session.add(brand)
        await session.flush()  # flush = INSERT sans commit
        logger.info(f"  Created brand: {name}")
    
    return brand


async def get_category(session: AsyncSession, slug: str) -> Category:
    """Récupère une catégorie par son slug."""
    result = await session.execute(
        select(Category).where(Category.slug == slug)
    )
    return result.scalar_one_or_none()


# ─────────────────────────────────────────────────────────────
# GPU INGESTION
# ─────────────────────────────────────────────────────────────

async def ingest_gpus(session: AsyncSession, filepath: Path) -> int:
    """
    Charge les GPUs depuis All_GPUs.csv.
    Adapte automatiquement aux colonnes disponibles.
    """
    logger.info(f"Loading GPUs from {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8-sig', on_bad_lines='skip')
    logger.info(f"  Found {len(df)} rows, columns: {list(df.columns)}")
    
    gpu_category = await get_category(session, "gpu")
    if not gpu_category:
        logger.error("Category 'gpu' not found. Run SQL init first.")
        return 0
    
    count = 0
    
    for idx, row in df.iterrows():
        try:
            # ── Nom du produit ───────────────────────────────
            # Essayer plusieurs noms de colonnes possibles
            name = None
            for col in ['Product Name', 'Name', 'name', 'Model', 'GPU']:
                if col in df.columns and clean_str(row.get(col)):
                    name = clean_str(row[col])
                    break
            
            if not name:
                continue
            
            # ── Marque ───────────────────────────────────────
            brand_name = None
            for col in ['Manufacturer', 'Brand', 'brand', 'Vendor']:
                if col in df.columns and clean_str(row.get(col)):
                    brand_name = clean_str(row[col])
                    break
            
            if not brand_name:
                # Déduire la marque depuis le nom
                if any(x in name.upper() for x in ['RTX', 'GTX', 'GEFORCE']):
                    brand_name = 'NVIDIA'
                elif any(x in name.upper() for x in ['RX ', 'RADEON']):
                    brand_name = 'AMD'
                else:
                    brand_name = 'Unknown'
            
            brand = await get_or_create_brand(session, brand_name)
            
            # ── Specs (JSONB) ─────────────────────────────────
            specs = {}
            
            # Mapping flexible des colonnes
            col_map = {
                'architecture':   ['Architecture', 'GPU Architecture', 'Chip'],
                'vram_gb':        ['Memory Size', 'VRAM', 'Memory (GB)', 'Videocard Memory'],
                'vram_type':      ['Memory Type', 'VRAM Type'],
                'cuda_cores':     ['CUDA Cores', 'Shader Processors', 'Stream Processors'],
                'base_clock_mhz': ['Base Clock', 'Core Clock (MHz)', 'GPU Clock'],
                'boost_clock_mhz':['Boost Clock', 'Core Clock Boost (MHz)'],
                'tdp_watts':      ['TDP', 'Power Consumption', 'TDP (Watts)'],
                'pcie_version':   ['PCIe', 'PCI Express'],
                'release_year':   ['Release Year', 'Year', 'Launch Year'],
            }
            
            for spec_key, possible_cols in col_map.items():
                for col in possible_cols:
                    if col in df.columns and not pd.isna(row.get(col)):
                        val = row[col]
                        if spec_key in ('vram_gb', 'cuda_cores', 'base_clock_mhz',
                                       'boost_clock_mhz', 'tdp_watts', 'release_year'):
                            specs[spec_key] = clean_numeric(val)
                        else:
                            specs[spec_key] = clean_str(val)
                        break
            
            # ── Prix ──────────────────────────────────────────
            price = None
            for col in ['Price', 'price', 'Current Price', 'MSRP']:
                if col in df.columns:
                    price = clean_numeric(row.get(col))
                    if price:
                        break
            
            # ── Créer le produit ──────────────────────────────
            product = Product(
                name=name,
                brand_id=brand.id,
                category_id=gpu_category.id,
                price=price,
                stock=10,      # Stock fictif pour le projet
                specs=specs,
                description=f"{name} - {brand_name} GPU",
                is_active=True,
            )
            session.add(product)
            count += 1
            
            # Commit par batch de 100 pour les performances
            if count % 100 == 0:
                await session.flush()
                logger.info(f"  Processed {count} GPUs...")
        
        except Exception as e:
            logger.warning(f"  Row {idx} skipped: {e}")
            continue
    
    logger.info(f"  ✅ {count} GPUs loaded")
    return count


# ─────────────────────────────────────────────────────────────
# CPU INGESTION
# ─────────────────────────────────────────────────────────────

async def ingest_cpus(session: AsyncSession, filepath: Path) -> int:
    """Charge les CPUs depuis Intel_CPUs.csv."""
    logger.info(f"Loading CPUs from {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8-sig', on_bad_lines='skip')
    logger.info(f"  Found {len(df)} rows, columns: {list(df.columns)}")
    
    cpu_category = await get_category(session, "cpu")
    if not cpu_category:
        logger.error("Category 'cpu' not found.")
        return 0
    
    intel_brand = await get_or_create_brand(session, "Intel")
    count = 0
    
    for idx, row in df.iterrows():
        try:
            # ── Nom ───────────────────────────────────────────
            name = None
            for col in ['Product Name', 'Name', 'name', 'Processor Number']:
                if col in df.columns and clean_str(row.get(col)):
                    name = clean_str(row[col])
                    break
            
            if not name:
                continue
            
            # ── Specs ─────────────────────────────────────────
            specs = {"memory_support": "DDR4"}  # Défaut Intel
            
            col_map = {
                'cores':           ['# of Cores', 'Cores', 'Core Count', 'Nb of Cores'],
                'threads':         ['# of Threads', 'Threads', 'Thread Count'],
                'base_clock_ghz':  ['Processor Base Frequency', 'Base Freq', 'Base Frequency'],
                'boost_clock_ghz': ['Max Turbo Frequency', 'Boost Freq', 'Turbo Frequency'],
                'tdp_watts':       ['TDP', 'TDP (Watts)', 'Thermal Design Power'],
                'socket':          ['Sockets Supported', 'Socket', 'Socket Type'],
                'cache_l3_mb':     ['Cache', 'L3 Cache', 'L3 Cache Size'],
                'igpu':            ['Processor Graphics', 'Graphics'],
                'launch_date':     ['Launch Date', 'Launch Year', 'Release Year'],
            }
            
            for spec_key, possible_cols in col_map.items():
                for col in possible_cols:
                    if col in df.columns and not pd.isna(row.get(col)):
                        val = row[col]
                        if spec_key in ('cores', 'threads', 'tdp_watts'):
                            specs[spec_key] = clean_int(val)
                        elif spec_key in ('base_clock_ghz', 'boost_clock_ghz', 'cache_l3_mb'):
                            specs[spec_key] = clean_numeric(val)
                        elif spec_key == 'igpu':
                            specs[spec_key] = clean_str(val) not in (None, 'None', 'Not Present')
                        else:
                            specs[spec_key] = clean_str(val)
                        break
            
            # Détecter DDR5 pour les CPUs récents
            launch = clean_str(row.get('Launch Date', ''))
            if launch and any(y in str(launch) for y in ['2022', '2023', '2024']):
                if 'socket' in specs and specs['socket'] in ('FCLGA1700', 'LGA1700'):
                    specs['memory_support'] = 'DDR4/DDR5'
            
            price = None
            for col in ['Recommended Customer Price', 'Price', 'MSRP']:
                if col in df.columns:
                    price = clean_numeric(row.get(col))
                    if price:
                        break
            
            product = Product(
                name=name,
                brand_id=intel_brand.id,
                category_id=cpu_category.id,
                price=price,
                stock=10,
                specs=specs,
                description=f"{name} - Intel CPU",
                is_active=True,
            )
            session.add(product)
            count += 1
            
            if count % 100 == 0:
                await session.flush()
                logger.info(f"  Processed {count} CPUs...")
        
        except Exception as e:
            logger.warning(f"  Row {idx} skipped: {e}")
            continue
    
    logger.info(f"  ✅ {count} CPUs loaded")
    return count


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

async def main():
    logger.info("=" * 50)
    logger.info("  TECHCART — SQL Ingestion")
    logger.info("=" * 50)
    
    # Créer les tables si elles n'existent pas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Tables created/verified")
    
    async with AsyncSessionLocal() as session:
        # GPUs
        gpu_file = Path("data/raw/All_GPUs.csv")
        if gpu_file.exists():
            gpu_count = await ingest_gpus(session, gpu_file)
        else:
            logger.warning(f"GPU file not found: {gpu_file}")
            gpu_count = 0
        
        # CPUs
        cpu_file = Path("data/raw/Intel_CPUs.csv")
        if cpu_file.exists():
            cpu_count = await ingest_cpus(session, cpu_file)
        else:
            logger.warning(f"CPU file not found: {cpu_file}")
            cpu_count = 0
        
        await session.commit()
    
    logger.info("=" * 50)
    logger.info(f"✅ Ingestion complete!")
    logger.info(f"   GPUs loaded : {gpu_count}")
    logger.info(f"   CPUs loaded : {cpu_count}")
    logger.info(f"   Total       : {gpu_count + cpu_count} products")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())