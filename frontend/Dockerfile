FROM nginx:alpine

# Create a script to generate config.js with proper environment variables
RUN echo '#!/bin/sh' > /docker-entrypoint.d/30-config.sh && \
    echo 'cat > /usr/share/nginx/html/config.js << EOF' >> /docker-entrypoint.d/30-config.sh && \
    echo 'window.APP_CONFIG = {' >> /docker-entrypoint.d/30-config.sh && \
    echo '    API_BASE_URL: "${API_URL}",' >> /docker-entrypoint.d/30-config.sh && \
    echo '    WS_BASE_URL: "${WS_URL}"' >> /docker-entrypoint.d/30-config.sh && \
    echo '};' >> /docker-entrypoint.d/30-config.sh && \
    echo 'EOF' >> /docker-entrypoint.d/30-config.sh && \
    chmod +x /docker-entrypoint.d/30-config.sh

# Copy the frontend files
COPY . /usr/share/nginx/html

# Create nginx configuration for WebSocket proxy
RUN echo 'server {' > /etc/nginx/conf.d/default.conf && \
    echo '    listen 80;' >> /etc/nginx/conf.d/default.conf && \
    echo '    location / {' >> /etc/nginx/conf.d/default.conf && \
    echo '        root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '    location /api/ {' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_pass http://backend:8000/;' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_http_version 1.1;' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_set_header Host $host;' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '    location = /ws {' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_pass http://backend:8000/ws;' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_http_version 1.1;' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_set_header Upgrade $http_upgrade;' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_set_header Connection "upgrade";' >> /etc/nginx/conf.d/default.conf && \
    echo '        proxy_set_header Host $host;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '}' >> /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
