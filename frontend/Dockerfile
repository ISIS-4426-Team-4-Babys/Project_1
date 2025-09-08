# Use official lightweight Node.js 20 Alpine image
FROM node:18-alpine AS builder

# Set working directory inside container
WORKDIR /app

# Copy dependency definition files first to leverage Docker layer caching
COPY package*.json ./

RUN npm ci --no-audit --no-fund

# Copy the entire frontend source code into the container
COPY . .

# Build the Next.js application for production
RUN npm run build

# Set environment to production for optimized performance
ENV NODE_ENV=production

# Default port for Next.js in production mode
ENV PORT=3000

# Expose port so it can be mapped outside the container
EXPOSE 3000

# Run the Next.js production server
CMD ["npm", "start"]
