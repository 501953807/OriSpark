# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for layer caching
COPY package*.json ./

# Install dependencies (skip scripts to avoid allow-scripts warnings)
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage - serve static files with nginx
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
