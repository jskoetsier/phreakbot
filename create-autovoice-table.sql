-- Create the autovoice table
CREATE TABLE IF NOT EXISTS phreakbot_autovoice (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(150) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (channel)
);
