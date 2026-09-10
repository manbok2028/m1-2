const fs = require("fs");
const apiBaseUrl = process.env.API_BASE_URL || "http://localhost:8000";
fs.mkdirSync("js", { recursive: true });
fs.writeFileSync("js/runtime-config.js", `window.APP_CONFIG = { API_BASE_URL: ${JSON.stringify(apiBaseUrl)} };\n`);
