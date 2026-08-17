-- ============================================================================
-- 002_niches.sql — Niche taxonomy (Cross-Niching Guide Book 2.0, H. Ebeling)
-- Five lists that get cross-niched to create unique niches:
--   holiday × career × family_relation × pet × hobby  (40,000+ combos)
-- Seed data is loaded by db/seed_niches.py (idempotent upserts).
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE niche_category AS ENUM
        ('holiday', 'career', 'family_relation', 'pet', 'hobby');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS niche_items (
    id           BIGSERIAL PRIMARY KEY,
    category     niche_category NOT NULL,
    name         TEXT NOT NULL,
    -- Group within a category: '' for careers/hobbies; 'dog_breed'/'cat_breed'/
    -- 'other_pet' for pets; 'mom_name'/'dad_name'/... for family relations.
    subcategory  TEXT NOT NULL DEFAULT '',
    -- Holidays only:
    month        SMALLINT CHECK (month BETWEEN 1 AND 12),
    day_note     TEXT,                 -- '25', 'last Monday', 'varies'
    seasonality  TEXT,                 -- derived tag, e.g. 'Q4', 'summer'
    -- Commercial weight used to rank cross-niching suggestions (0 = default,
    -- higher = better seller). Seeded in db/seed_niches.py.
    popularity   SMALLINT NOT NULL DEFAULT 0,
    active       BOOLEAN NOT NULL DEFAULT true,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT niche_items_uniq UNIQUE (category, name, subcategory)
);

CREATE INDEX IF NOT EXISTS idx_niche_items_category ON niche_items (category);
CREATE INDEX IF NOT EXISTS idx_niche_items_month    ON niche_items (month);
CREATE INDEX IF NOT EXISTS idx_niche_items_active   ON niche_items (active);
