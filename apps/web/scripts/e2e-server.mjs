import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '../..');
const apiRoot = resolve(root, 'apps/api');
const webRoot = resolve(root, 'apps/web');

const env = {
  ...process.env,
  ROSCLAW_PRACTICE_DIR: resolve(apiRoot, 'tests/fixtures/practice_runs'),
  ROSCLAW_DATABASE_URL: 'sqlite:///:memory:',
  ROSCLAW_EXPORT_DIR: resolve(root, 'tmp/e2e-exports'),
};

const children = [];

function spawnAndWait(cmd, args, cwd) {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(cmd, args, {
      cwd,
      env,
      stdio: 'inherit',
      shell: false,
    });
    children.push(child);
    child.on('error', reject);
    resolvePromise(child);
  });
}

async function waitForUrl(url, timeoutMs = 60_000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status < 500) return;
    } catch {
      // retry
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function main() {
  await spawnAndWait('python3', ['-m', 'uvicorn', 'src.main:app', '--port', '8001', '--reload'], apiRoot);
  await waitForUrl('http://127.0.0.1:8001/health');

  await spawnAndWait(resolve(webRoot, 'node_modules/.bin/next'), ['dev', '--port', '3000'], webRoot);
  await waitForUrl('http://127.0.0.1:3000');

  console.log('E2E dev server ready (API 8001 + Web 3000)');
}

function shutdown() {
  for (const child of children) {
    child.kill('SIGTERM');
  }
  setTimeout(() => process.exit(0), 500);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

main().catch((err) => {
  console.error(err);
  shutdown();
});
