-- ============================================================================
-- 001_keywords.sql — Keywords base (Appendix B.2 of the POD Factory OS manual)
-- Combines the manual's model with the eRank export columns
-- (eRank_-_Bulk_Keywords.csv) and the objective validation result.
-- Metric conventions (same as tools/erank_tools.py):
--   search_volume = 0    -> eRank's "< 20" value (~null demand)
--   NULL                 -> "Unknown" or empty in the export
-- ============================================================================

-- Enums (idempotent in case this is run by hand outside the automatic init).
DO $$ BEGIN
    CREATE TYPE keyword_decision AS ENUM
        ('pending', 'fit', 'unfit', 'trap', 'to_design', 'discarded');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE buyer_intent AS ENUM
        ('gift_other', 'gift_self', 'occasion', 'decor', 'other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- SOP v1.1 keyword axes, ordered by measured performance.
DO $$ BEGIN
    CREATE TYPE keyword_axis AS ENUM
        ('cohort', 'age', 'formula', 'family_role', 'hobby', 'occupational',
         'occasion', 'other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS keywords (
    id                 BIGSERIAL PRIMARY KEY,
    keyword            TEXT NOT NULL,
    niche              TEXT,
    cross_niche        TEXT,
    intent             buyer_intent,
    seasonality        TEXT,                 -- 'Q4', 'Halloween', 'Christmas', ...
    -- eRank / EverBee metrics
    search_volume      INTEGER,              -- Avg Searches (0 = "< 20", NULL = Unknown)
    avg_clicks         INTEGER,              -- Avg Clicks
    ctr                NUMERIC(6,2),         -- Avg CTR in % (e.g. 147.00)
    competition        INTEGER,              -- Etsy Competition (listings)
    difficulty         SMALLINT CHECK (difficulty BETWEEN 0 AND 100),  -- KD 0-100
    source             TEXT NOT NULL DEFAULT 'eRank',
    -- SOP v1.1 fields
    axis               keyword_axis,         -- cohort/age/formula/family_role/...
    -- Ratio R = searches / competition (SOP: >=0.02 green, <0.01 red). Auto-computed.
    ratio_r            NUMERIC(8,5) GENERATED ALWAYS AS (
                           CASE WHEN search_volume > 0 AND competition > 0
                                THEN round(search_volume::numeric / competition, 5)
                                ELSE NULL END
                       ) STORED,
    -- head (<=2 words) / mid (3) / long_tail (4+). Auto-computed from the keyword.
    keyword_type       TEXT GENERATED ALWAYS AS (
                           CASE
                             WHEN array_length(string_to_array(btrim(keyword), ' '), 1) <= 2 THEN 'head'
                             WHEN array_length(string_to_array(btrim(keyword), ' '), 1) = 3 THEN 'mid'
                             ELSE 'long_tail'
                           END
                       ) STORED,
    -- Validation (computed by code per SOP; see tools/sop_validation.py)
    decision           keyword_decision NOT NULL DEFAULT 'pending',
    validation_reason  TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- A keyword may exist in several niches, but not duplicated within one.
    CONSTRAINT keywords_keyword_niche_uniq UNIQUE (keyword, niche)
);

CREATE INDEX IF NOT EXISTS idx_keywords_niche       ON keywords (niche);
CREATE INDEX IF NOT EXISTS idx_keywords_decision    ON keywords (decision);
CREATE INDEX IF NOT EXISTS idx_keywords_seasonality ON keywords (seasonality);

-- Keep updated_at current on every UPDATE.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_keywords_updated ON keywords;
CREATE TRIGGER trg_keywords_updated
    BEFORE UPDATE ON keywords
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
