FROM node:18-alpine

WORKDIR /app

# Copy configuration files first
COPY package*.json ./
COPY postcss.config.cjs ./
COPY tailwind.config.cjs ./
COPY vite.config.js ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port 3000
EXPOSE 3000

# Start the application
CMD ["npm", "run", "dev"]