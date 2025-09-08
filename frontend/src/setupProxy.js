// src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');
const { parse } = require('url');

module.exports = function (app) {
  // API normal
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://backend:8000',
      changeOrigin: true,
      pathRewrite: { '^/api': '' },
    })
  );

  // /agent -> vhost agent_<id>.localhost (manejados por tu reverse proxy local)
  app.use(
    '/agent',
    createProxyMiddleware({
      // ⬅️ pon aquí el puerto donde escucha tu reverse proxy (80, 8080, 8000, etc.)
      target: 'http://nginx-proxy:80',
      changeOrigin: true,

      // Acepta /agent y /agent/ask; siempre reescribe a /ask (conserva query)
      pathRewrite: (path, req) => {
        const { query } = parse(req.url, true);
        // @ts-ignore
        const search = new URLSearchParams(query);
        return `/ask${search.toString() ? `?${search.toString()}` : ''}`;
      },

      // Siempre mismo origen; la selección real va por el Host header
      router: () => 'http://nginx-proxy:80',

      // Setea Host para que nginx-proxy/Traefik rote al contenedor correcto
      onProxyReq: (proxyReq, req) => {
        const { query } = parse(req.url, true);
        const id = query.agentID;
        if (id) {
          const vhost = `agent_${id}`;
          proxyReq.setHeader('host', vhost);
        }
      },
    })
  );
};
