const dns = require("node:dns");
const net = require("node:net");
const http = require("node:http");

const originalLookup = dns.lookup;
dns.lookup = function lookup(hostname, ...args) {
  return originalLookup.call(this, hostname === "api" ? "127.0.0.1" : hostname, ...args);
};

const upstreamPort = Number(process.env.ROUTING_UPSTREAM_PORT);
function rewriteOptions(options) {
  if (options && typeof options === "object" && (options.hostname === "api" || options.host === "api") && Number(options.port) === 8000) {
    return { ...options, hostname: "127.0.0.1", host: "127.0.0.1", port: upstreamPort };
  }
  return options;
}
const originalRequest = http.request;
http.request = function request(options, ...args) {
  return originalRequest.call(this, rewriteOptions(options), ...args);
};
const originalCreateConnection = net.createConnection;
function createConnection(...args) {
  const first = args[0];
  args[0] = rewriteOptions(first);
  return originalCreateConnection.apply(this, args);
}
net.createConnection = createConnection;
net.connect = createConnection;
