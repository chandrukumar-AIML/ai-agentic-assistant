-- backend/billing/create_billing_tables.sql
-- Billing tiers and usage tracking

CREATE TABLE IF NOT EXISTS billing_subscriptions (
    id              BIGSERIAL   PRIMARY KEY,
    user_id         TEXT        NOT NULL UNIQUE,
    workspace_id    TEXT        NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',

    plan_tier       TEXT        NOT NULL DEFAULT 'free'
                    CHECK (plan_tier IN ('free','pro','enterprise')),

    -- Payment provider info
    provider        TEXT        CHECK (provider IN ('stripe','razorpay','manual')),
    provider_sub_id TEXT,       -- Stripe subscription_id or Razorpay subscription_id
    provider_cust_id TEXT,      -- Stripe customer_id or Razorpay customer_id

    -- Billing cycle
    billing_cycle   TEXT        DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly','annual')),
    current_period_start TIMESTAMPTZ,
    current_period_end   TIMESTAMPTZ,

    -- Status
    status          TEXT        NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active','past_due','cancelled','trialing')),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_user      ON billing_subscriptions (user_id);
CREATE INDEX IF NOT EXISTS idx_billing_workspace  ON billing_subscriptions (workspace_id);

-- Monthly usage tracking
CREATE TABLE IF NOT EXISTS billing_usage (
    id              BIGSERIAL   PRIMARY KEY,
    user_id         TEXT        NOT NULL,
    workspace_id    TEXT        NOT NULL,
    month           DATE        NOT NULL,   -- first day of month e.g. 2025-06-01

    -- Counters
    api_calls       INT         NOT NULL DEFAULT 0,
    tokens_used     BIGINT      NOT NULL DEFAULT 0,
    image_gens      INT         NOT NULL DEFAULT 0,
    audio_mins      FLOAT       NOT NULL DEFAULT 0.0,
    storage_mb      FLOAT       NOT NULL DEFAULT 0.0,

    UNIQUE (user_id, month)
);

CREATE INDEX IF NOT EXISTS idx_usage_user_month ON billing_usage (user_id, month);
