
-- Ce fichier s'exécute automatiquement au premier démarrage
-- de PostgreSQL via le volume ./sql:/docker-entrypoint-initdb.d
-- ══════════════════════════════════════════════════════════════

-- Active les extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- génération d'UUIDs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
-- recherche textuelle fuzzy

-- ─────────────────────────────────────────────────────────────
-- TABLE 1 : CATEGORIES
-- Hiérarchie des produits (Electronics > GPU, CPU, etc.)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    -- slug = version URL-friendly : "Graphics Cards" → "graphics-cards"
    description TEXT,
    parent_id INTEGER REFERENCES categories (id) ON DELETE SET NULL,
    -- parent_id permet la hiérarchie : GPU est sous Electronics
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW()
);

-- Index sur slug pour les lookups rapides
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories (slug);

-- Données initiales
INSERT INTO
    categories (name, slug, description)
VALUES (
        'Electronics',
        'electronics',
        'All electronic components'
    ),
    (
        'Graphics Cards',
        'gpu',
        'Graphics Processing Units'
    ),
    (
        'Processors',
        'cpu',
        'Central Processing Units'
    ),
    (
        'Memory',
        'ram',
        'RAM modules'
    ),
    (
        'Storage',
        'storage',
        'SSDs and HDDs'
    ),
    (
        'Motherboards',
        'motherboard',
        'Motherboards'
    ) ON CONFLICT (slug) DO NOTHING;

-- Établir la hiérarchie
UPDATE categories
SET
    parent_id = (
        SELECT id
        FROM categories
        WHERE
            slug = 'electronics'
    )
WHERE
    slug IN (
        'gpu',
        'cpu',
        'ram',
        'storage',
        'motherboard'
    );

-- ─────────────────────────────────────────────────────────────
-- TABLE 2 : BRANDS
-- Fabricants des produits
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100),
    website VARCHAR(255),
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_brands_slug ON brands (slug);

-- Données initiales
INSERT INTO
    brands (name, slug, country)
VALUES (
        'NVIDIA',
        'nvidia',
        'United States'
    ),
    ('AMD', 'amd', 'United States'),
    (
        'Intel',
        'intel',
        'United States'
    ),
    ('ASUS', 'asus', 'Taiwan'),
    ('MSI', 'msi', 'Taiwan'),
    (
        'Gigabyte',
        'gigabyte',
        'Taiwan'
    ),
    (
        'EVGA',
        'evga',
        'United States'
    ),
    (
        'Sapphire',
        'sapphire',
        'Hong Kong'
    ),
    (
        'PowerColor',
        'powercolor',
        'Hong Kong'
    ),
    ('Zotac', 'zotac', 'Hong Kong') ON CONFLICT (slug) DO NOTHING;

-- ─────────────────────────────────────────────────────────────
-- TABLE 3 : PRODUCTS (Table principale)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS products (
    -- Identification
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(100) UNIQUE,
    -- sku = Stock Keeping Unit = identifiant unique du produit
    -- ex: "GPU-RTX4070-ASUS-001"
    
    name            VARCHAR(300) NOT NULL,

-- Relations
brand_id INTEGER REFERENCES brands (id) ON DELETE SET NULL,
category_id INTEGER REFERENCES categories (id) ON DELETE SET NULL,

-- Prix et stock
price DECIMAL(10, 2),
-- DECIMAL(10,2) = jusqu'à 99999999.99 avec 2 décimales
-- On utilise DECIMAL et pas FLOAT pour éviter les erreurs d'arrondi
-- (0.1 + 0.2 = 0.30000000000000004 en float !)
stock INTEGER NOT NULL DEFAULT 0,

-- Spécifications techniques (JSONB)
-- JSONB = JSON stocké en binaire, indexable, plus rapide que JSON
specs JSONB DEFAULT '{}',
/*
Exemples de contenu :

GPU : {
"architecture": "Ada Lovelace",
"vram_gb": 12,
"vram_type": "GDDR6X",
"cuda_cores": 7168,
"base_clock_mhz": 2310,
"boost_clock_mhz": 2610,
"tdp_watts": 200,
"pcie_version": "4.0",
"outputs": "3x DisplayPort 1.4, 1x HDMI 2.1"
}

CPU : {
"cores": 16,
"threads": 32,
"base_clock_ghz": 4.5,
"boost_clock_ghz": 5.7,
"tdp_watts": 170,
"socket": "AM5",
"cache_l3_mb": 64,
"memory_support": "DDR5",
"igpu": false
}
*/

-- Description longue (aussi stockée dans Vector DB pour la recherche)
description TEXT,

-- Statut
is_active BOOLEAN NOT NULL DEFAULT TRUE,

-- Timestamps
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── INDEX sur products ────────────────────────────────────────

-- Index sur les clés étrangères (toujours indexer les FK)
CREATE INDEX IF NOT EXISTS idx_products_brand_id ON products (brand_id);

CREATE INDEX IF NOT EXISTS idx_products_category_id ON products (category_id);

-- Index sur le prix (pour les filtres "moins de X€")
CREATE INDEX IF NOT EXISTS idx_products_price ON products (price);

-- Index sur le stock (pour filtrer "en stock seulement")
CREATE INDEX IF NOT EXISTS idx_products_stock ON products (stock);

-- Index GIN sur JSONB (pour chercher dans les specs)
-- GIN = Generalized Inverted Index, optimal pour JSONB
-- Permet : WHERE specs->>'socket' = 'AM5'
CREATE INDEX IF NOT EXISTS idx_products_specs ON products USING GIN (specs);

-- Index pour la recherche textuelle sur le nom
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING GIN (name gin_trgm_ops);
-- Permet : WHERE name ILIKE '%RTX 4070%' de façon efficace

-- Index composé pour les requêtes courantes
CREATE INDEX IF NOT EXISTS idx_products_category_active ON products (category_id, is_active);

-- ─────────────────────────────────────────────────────────────
-- TRIGGER : Mise à jour automatique de updated_at
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    -- NEW = la nouvelle ligne en cours d'insertion/update
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
-- Quand tu fais UPDATE products SET price = 599 WHERE id = 1
-- → updated_at est automatiquement mis à NOW()

-- ─────────────────────────────────────────────────────────────
-- TABLE 4 : PRODUCT IMAGES
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    -- ON DELETE CASCADE : si le produit est supprimé, ses images aussi
    url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(300),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_product_images_product_id ON product_images (product_id);

-- ─────────────────────────────────────────────────────────────
-- TABLE 5 : COMPATIBILITY RULES
-- Règles de compatibilité entre composants
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS compatibility_rules (
    id          SERIAL PRIMARY KEY,

-- Composant A
category_a VARCHAR(50) NOT NULL, -- ex: 'cpu'
spec_key_a VARCHAR(50) NOT NULL, -- ex: 'socket'
spec_val_a VARCHAR(100) NOT NULL, -- ex: 'AM5'

-- Composant B
category_b VARCHAR(50) NOT NULL, -- ex: 'motherboard'
spec_key_b VARCHAR(50) NOT NULL, -- ex: 'socket'
spec_val_b VARCHAR(100) NOT NULL, -- ex: 'AM5'

-- Type de relation
is_compatible   BOOLEAN NOT NULL DEFAULT TRUE,
    -- TRUE  = ces specs sont compatibles
    -- FALSE = ces specs sont INCOMPATIBLES (conflit)
    
    note        TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Exemples de données de compatibilité
INSERT INTO
    compatibility_rules (
        category_a,
        spec_key_a,
        spec_val_a,
        category_b,
        spec_key_b,
        spec_val_b,
        note
    )
VALUES (
        'cpu',
        'socket',
        'AM5',
        'motherboard',
        'socket',
        'AM5',
        'AMD AM5 CPUs require AM5 motherboards (DDR5 only)'
    ),
    (
        'cpu',
        'socket',
        'AM4',
        'motherboard',
        'socket',
        'AM4',
        'AMD AM4 CPUs require AM4 motherboards'
    ),
    (
        'cpu',
        'socket',
        'LGA1700',
        'motherboard',
        'socket',
        'LGA1700',
        'Intel 12th/13th/14th gen CPUs use LGA1700'
    ),
    (
        'cpu',
        'socket',
        'LGA1851',
        'motherboard',
        'socket',
        'LGA1851',
        'Intel Core Ultra 200 CPUs use LGA1851'
    ),
    (
        'cpu',
        'memory_support',
        'DDR5',
        'ram',
        'type',
        'DDR5',
        'AM5 platform only supports DDR5'
    ),
    (
        'cpu',
        'memory_support',
        'DDR4',
        'ram',
        'type',
        'DDR4',
        'Older platforms use DDR4'
    ) ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────────
-- TABLE 6 : PRICE HISTORY
-- Historique des prix (utile pour les tendances)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    price DECIMAL(10, 2) NOT NULL,
    recorded_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history (product_id);

CREATE INDEX IF NOT EXISTS idx_price_history_recorded_at ON price_history (recorded_at);

-- ─────────────────────────────────────────────────────────────
-- VUES (VIEWS) — Requêtes pré-construites courantes
-- ─────────────────────────────────────────────────────────────

-- Vue : tous les produits avec leurs infos complètes
CREATE OR REPLACE VIEW v_products_full AS
SELECT
    p.id,
    p.sku,
    p.name,
    p.price,
    p.stock,
    p.specs,
    p.description,
    p.is_active,
    b.name AS brand_name,
    b.slug AS brand_slug,
    c.name AS category_name,
    c.slug AS category_slug,
    p.created_at,
    p.updated_at
FROM
    products p
    LEFT JOIN brands b ON p.brand_id = b.id
    LEFT JOIN categories c ON p.category_id = c.id;

-- Vue : GPUs uniquement avec specs extraites
CREATE OR REPLACE VIEW v_gpus AS
SELECT 
    p.id,
    p.name,
    p.price,
    p.stock,
    b.name                          AS brand,
    p.specs->>'architecture'        AS architecture,
    (p.specs->>'vram_gb')::NUMERIC  AS vram_gb,
    p.specs->>'vram_type'           AS vram_type,
    (p.specs->>'cuda_cores')::INT   AS cuda_cores,
    (p.specs->>'tdp_watts')::INT    AS tdp_watts,
    (p.specs->>'boost_clock_mhz')::INT AS boost_clock_mhz
FROM products p
JOIN brands b ON p.brand_id = b.id
JOIN categories c ON p.category_id = c.id
WHERE c.slug = 'gpu' AND p.is_active = TRUE;

-- Vue : CPUs uniquement avec specs extraites
CREATE OR REPLACE VIEW v_cpus AS
SELECT 
    p.id,
    p.name,
    p.price,
    p.stock,
    b.name                              AS brand,
    (p.specs->>'cores')::INT            AS cores,
    (p.specs->>'threads')::INT          AS threads,
    (p.specs->>'base_clock_ghz')::NUMERIC AS base_clock_ghz,
    (p.specs->>'boost_clock_ghz')::NUMERIC AS boost_clock_ghz,
    (p.specs->>'tdp_watts')::INT        AS tdp_watts,
    p.specs->>'socket'                  AS socket,
    p.specs->>'memory_support'          AS memory_support,
    (p.specs->>'cache_l3_mb')::NUMERIC  AS cache_l3_mb
FROM products p
JOIN brands b ON p.brand_id = b.id
JOIN categories c ON p.category_id = c.id
WHERE c.slug = 'cpu' AND p.is_active = TRUE;

-- ─────────────────────────────────────────────────────────────
-- CONFIRMATION
-- ─────────────────────────────────────────────────────────────
DO $$
BEGIN
    RAISE NOTICE '✅ TechCart schema created successfully';
    RAISE NOTICE '   Tables: categories, brands, products, product_images';
    RAISE NOTICE '   Tables: compatibility_rules, price_history';
    RAISE NOTICE '   Views: v_products_full, v_gpus, v_cpus';
END $$;