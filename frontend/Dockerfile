FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package.json ./
RUN npm install

# Copy frontend source code
COPY . .

# Expose port
EXPOSE 3000

# Run in development mode to support dynamic environment variable loading
CMD ["npm", "run", "dev"]
