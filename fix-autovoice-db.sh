#!/bin/bash
# Script to fix the autovoice database table

# Connect to the PostgreSQL database and fix the autovoice table
docker-compose exec -T postgres psql -U phreakbot -d phreakbot << 'EOF'
-- First, rollback any aborted transactions
ROLLBACK;

-- Drop the autovoice table if it exists
DROP TABLE IF EXISTS phreakbot_autovoice;

-- Create the autovoice table with the correct structure
CREATE TABLE phreakbot_autovoice (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(150) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (channel)
);

-- Verify the table was created
\dt phreakbot_autovoice

-- Test a simple query
SELECT * FROM phreakbot_autovoice;
EOF

echo "Database fix completed. Restarting the bot..."
docker-compose restart phreakbot
