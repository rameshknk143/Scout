-- Explicit migration; additive only. Apply before deploying schema-aware collectors.
CREATE TABLE IF NOT EXISTS public.field_observations (
  observation_id TEXT PRIMARY KEY CHECK (observation_id ~ '^[a-f0-9]{64}$'),
  marketplace TEXT NOT NULL,
  asin TEXT NOT NULL CHECK (asin ~ '^[A-Z0-9]{10}$'),
  field_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  schema_version TEXT NOT NULL,
  status TEXT NOT NULL,
  unit TEXT,
  raw_value JSONB NOT NULL,
  normalized_value JSONB NOT NULL,
  context JSONB NOT NULL DEFAULT '{}'::JSONB,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (status <> 'COLLECTED' OR normalized_value <> 'null'::JSONB)
);
CREATE INDEX IF NOT EXISTS field_observations_history
  ON public.field_observations(marketplace,asin,field_key,observed_at DESC);
-- No UPDATE/DELETE operations are used by the application. Run the migration
-- as owner and use a separate collector role with INSERT/SELECT only in production.
ALTER TABLE public.field_observations ENABLE ROW LEVEL SECURITY;
-- No anonymous/public policy: operational access uses the private DB connection.
