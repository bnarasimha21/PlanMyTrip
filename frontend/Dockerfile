FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (need dev dependencies for build)
RUN npm ci

# Copy frontend source
COPY . ./

# Build-time args for Vite env (only VITE_* are exposed to client)
ARG VITE_API_BASE
ARG VITE_MAPBOX_TOKEN
ARG VITE_GOOGLE_CLIENT_ID

# Export as env so the build step can read them
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

# Create a non-root user first
RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 --ingroup nodejs appuser

# Build the Vite app (outputs to dist)
RUN npm run build
# Add build timestamp to force fresh deployments
RUN sh -c 'echo "Build timestamp: $(date)" > dist/build-info.txt'

# Verify build directory exists and has content
RUN ls -la dist/ \
  && test -f dist/index.html

# Change ownership of the app directory to non-root user
RUN chown -R appuser:nodejs /app
USER appuser

# Expose port
EXPOSE 3000

# Health check (requires busybox wget available in alpine)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Serve the built Vite app
# Use npx serve to avoid adding it to dependencies
CMD ["npx", "serve", "-s", "dist", "-l", "3000"]