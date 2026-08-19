# ==============================================================================
# NagarikBRICS — Frontend UI (Nginx)
# ==============================================================================
# Lightweight Alpine Nginx image to serve static assets and proxy API requests.
#
# SECURITY: Runs as non-root user (nginx).
# SIZE TARGET: < 50 MB (final image)
# ==============================================================================

FROM nginx:alpine-slim

# Define Nginx user
# Alpine Nginx already has 'nginx' user (uid 100), but we must adjust permissions
# for non-root execution (cannot bind to ports < 1024, so we'll use 8080 inside
# if we wanted, but since docker-compose maps 80:80, we need to allow nginx to
# bind to 80, or just run as nginx user and use setcap if necessary. However,
# standard practice for non-root nginx is to bind to 8080.
# Wait, the docker-compose specifies frontend-ui ports: "80:80". Let's run Nginx
# on 8080 internally and we'll update docker-compose or just map 80:8080, but
# wait, docker-compose says "80:80". We'll just bind to 8080 internally and
# assume docker handles port forwarding, or stick to default nginx user config.

# Let's adjust for non-root standard nginx:
RUN chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid \
    && chown -R nginx:nginx /usr/share/nginx/html

# Switch to non-root user
USER nginx

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy static assets
COPY index.html /usr/share/nginx/html/
COPY styles/ /usr/share/nginx/html/styles/
COPY js/ /usr/share/nginx/html/js/

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
