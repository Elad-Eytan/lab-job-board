'use strict';

const fs = require('fs');

const { Pool } = require('pg');

let databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  const passwordFile = 
    process.env.POSTGRES_PASSWORD_FILE || '/run/secrets/db_password';
  const password = fs.readFileSync(passwordFile, 'utf8').trim();
  const encodedPassword = encodeURIComponent(password);
  const databaseUser = process.env.POSTGRES_USER || 'postgres';
  const databaseHost = process.env.POSTGRES_HOST || 'postgres';
  const databaseName = process.env.POSTGRES_DB || 'jobboard';

  databaseUrl = 
  `postgresql://${databaseUser}:${encodedPassword}` +
    `@${databaseHost}:5432/${databaseName}`;

}

const pool = new Pool({
  connectionString: databaseUrl,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pool.on('error', (err) => {
  console.error('Unexpected database pool error:', err.message);
});

async function initDB() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS applications (
      id              UUID         PRIMARY KEY,
      job_id          VARCHAR(255) NOT NULL,
      applicant_name  VARCHAR(200) NOT NULL,
      applicant_email VARCHAR(200) NOT NULL,
      cover_letter    TEXT,
      status          VARCHAR(50)  DEFAULT 'pending'
                      CHECK (status IN ('pending', 'reviewed', 'accepted', 'rejected')),
      created_at      TIMESTAMP    DEFAULT NOW()
    )
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id)
  `);

  console.log('[db] Applications table ready');
}

module.exports = { pool, initDB };
