/** @type {import('next').NextConfig} */
const fs = require('fs');
const path = require('path');

// Manually load root .env to ensure Next.js sees it
try {
  const rootEnvPath = path.resolve(__dirname, '../.env');
  if (fs.existsSync(rootEnvPath)) {
    const envFile = fs.readFileSync(rootEnvPath, 'utf8');
    envFile.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split('=');
      const value = valueParts.join('=');
      if (key && value) {
        process.env[key.trim()] = value.trim();
      }
    });
  }
} catch (e) {
  console.error('Failed to load root .env in next.config.js:', e);
}

const nextConfig = {
  // Use standalone output for easier Docker/Production deployment
  output: 'standalone',
};

module.exports = nextConfig;
