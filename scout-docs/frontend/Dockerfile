FROM node:18-alpine

# Create non-root user early
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# Create app directory with proper ownership
RUN mkdir -p /app && chown nextjs:nodejs /app

WORKDIR /app

# Copy package files with correct ownership
COPY --chown=nextjs:nodejs package*.json ./

# Switch to non-root user and install dependencies
USER nextjs
RUN npm install

# Copy source code with correct ownership (avoids chown -R)
COPY --chown=nextjs:nodejs . .

EXPOSE 3000

CMD ["npm", "start"]