-- =============================================================================
-- EduForge Database Initialization Script
-- Creates required PostgreSQL extensions and schemas for all microservices.
-- This script runs automatically on first database creation via
-- docker-entrypoint-initdb.d.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Schemas (one per microservice)
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS identity;
COMMENT ON SCHEMA identity IS 'Authentication, authorization, users, tenants, and roles';

CREATE SCHEMA IF NOT EXISTS portal;
COMMENT ON SCHEMA portal IS 'Admin and teacher dashboard data';

CREATE SCHEMA IF NOT EXISTS exam;
COMMENT ON SCHEMA exam IS 'Question banks, tests, proctoring, and grading';

CREATE SCHEMA IF NOT EXISTS notification;
COMMENT ON SCHEMA notification IS 'WhatsApp, SMS, email, and push notification logs';

CREATE SCHEMA IF NOT EXISTS billing;
COMMENT ON SCHEMA billing IS 'Fee management, invoices, and payment records';

CREATE SCHEMA IF NOT EXISTS ai;
COMMENT ON SCHEMA ai IS 'AI/ML service data - question generation, evaluations';

CREATE SCHEMA IF NOT EXISTS analytics;
COMMENT ON SCHEMA analytics IS 'Reports, aggregations, and dashboard metrics';

-- ---------------------------------------------------------------------------
-- Grant privileges to the application user
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    schema_name TEXT;
BEGIN
    FOR schema_name IN
        SELECT unnest(ARRAY['identity', 'portal', 'exam', 'notification', 'billing', 'ai', 'analytics'])
    LOOP
        EXECUTE format('GRANT ALL PRIVILEGES ON SCHEMA %I TO %I', schema_name, current_user);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON TABLES TO %I', schema_name, current_user);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON SEQUENCES TO %I', schema_name, current_user);
    END LOOP;
END
$$;
