import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { randomInt } from "node:crypto";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const appRoot = new URL("..", import.meta.url);
const routesManifest = JSON.parse(await readFile(new URL("../.next/routes-manifest.json", import.meta.url), "utf8"));
const rewrite = routesManifest.rewrites?.afterFiles?.find((candidate) => candidate.source === "/api/:path*");

if (rewrite?.destination !== "http://api:8000/:path*") {
  throw new Error("Built route manifest does not map /api/:path* to http://api:8000/:path*.");
}

const upstreamRequests = [];
const upstream = createServer((request, response) => {
  upstreamRequests.push(request.url);
  response.writeHead(200, { "Content-Type": "application/json" });
  response.end(JSON.stringify({ routed: true, path: request.url }));
});
await new Promise((resolve, reject) => {
  upstream.once("error", reject);
  upstream.listen(0, "127.0.0.1", resolve);
});
const upstreamAddress = upstream.address();
if (upstreamAddress === null || typeof upstreamAddress === "string") throw new Error("Could not determine the routing probe port.");
const upstreamPort = upstreamAddress.port;

const appPort = randomInt(3200, 3900);
const app = spawn(process.execPath, [fileURLToPath(new URL("./.next/standalone/server.js", appRoot))], {
  cwd: fileURLToPath(appRoot),
  env: {
    ...process.env,
    API_ORIGIN: "http://api:8000",
    HOSTNAME: "127.0.0.1",
    NODE_ENV: "production",
    NEXT_TELEMETRY_DISABLED: "1",
    PORT: String(appPort),
    ROUTING_UPSTREAM_PORT: String(upstreamPort),
    NODE_OPTIONS: [process.env.NODE_OPTIONS, `--require=${new URL("./route-dns-shim.cjs", import.meta.url).pathname}`].filter(Boolean).join(" "),
  },
  stdio: ["ignore", "pipe", "pipe"],
});
let appOutput = "";
let appError;
app.once("error", (error) => { appError = error; });
app.stdout.on("data", (chunk) => { appOutput += chunk; });
app.stderr.on("data", (chunk) => { appOutput += chunk; });
const appClosed = new Promise((resolve) => app.once("close", resolve));

async function waitForApp() {
  const url = `http://127.0.0.1:${appPort}/`;
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (appError) throw appError;
    if (app.exitCode !== null) throw new Error(`Built web server exited early.\n${appOutput}`);
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // The standalone server may still be booting.
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out waiting for the built web server.\n${appOutput}`);
}

try {
  await waitForApp();
  const response = await fetch(`http://127.0.0.1:${appPort}/api/routing-probe`);
  const payload = await response.json();
  if (!response.ok || payload.routed !== true || payload.path !== "/routing-probe" || upstreamRequests.length !== 1) {
    throw new Error(`Built /api rewrite did not reach the API service: ${response.status} ${JSON.stringify(payload)}.`);
  }
  process.stdout.write("Docker routing verification passed: built /api routes to http://api:8000.\n");
} finally {
  if (app.exitCode === null) app.kill("SIGTERM");
  await appClosed;
  await new Promise((resolve) => upstream.close(resolve));
}
