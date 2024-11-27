FROM nginx:alpine

# Create a script to generate config.js with proper environment variables
RUN echo '#!/bin/sh' > /docker-entrypoint.d/30-config.sh && \
    echo 'cat > /usr/share/nginx/html/config.js << EOF' >> /docker-entrypoint.d/30-config.sh && \
    echo 'window.APP_CONFIG = {' >> /docker-entrypoint.d/30-config.sh && \
    echo '    API_BASE_URL: "${API_URL}",' >> /docker-entrypoint.d/30-config.sh && \
    echo '    WS_BASE_URL: "${API_URL}".replace(/^http/, "ws")' >> /docker-entrypoint.d/30-config.sh && \
    echo '};' >> /docker-entrypoint.d/30-config.sh && \
    echo 'EOF' >> /docker-entrypoint.d/30-config.sh && \
    chmod +x /docker-entrypoint.d/30-config.sh

# Copy the frontend files
COPY . /usr/share/nginx/html

# Create nginx configuration for WebSocket proxy
RUN echo 'server { \n\
    listen 80; \n\
    location / { \n\
        root /usr/share/nginx/html; \n\
        try_files $uri $uri/ /index.html; \n\
    } \n\
    location /ws { \n\
        proxy_pass http://backend:8000; \n\
        proxy_http_version 1.1; \n\
        proxy_set_header Upgrade $http_upgrade; \n\
        proxy_set_header Connection "upgrade"; \n\
        proxy_set_header Host $host; \n\
    } \n\
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
