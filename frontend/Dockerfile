FROM nginx:alpine

# Create a script to generate config.js
RUN echo '#!/bin/sh' > /docker-entrypoint.d/30-config.sh && \
    echo 'echo "window.APP_CONFIG = { API_BASE_URL: \"${API_URL}\" };" > /usr/share/nginx/html/config.js' >> /docker-entrypoint.d/30-config.sh && \
    chmod +x /docker-entrypoint.d/30-config.sh

# Copy the frontend files
COPY . /usr/share/nginx/html

# Copy custom nginx configuration if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
