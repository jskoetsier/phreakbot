CREATE TABLE IF NOT EXISTS phreakbot_autoop (
    id SERIAL,
    users_id INT NOT NULL,
    channel VARCHAR(150) NOT NULL DEFAULT '',
    PRIMARY KEY (id, users_id, channel),
    UNIQUE (users_id, channel),
    CONSTRAINT phreakbot_autoop_users_id_fkey FOREIGN KEY (users_id)
      REFERENCES phreakbot_users (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
