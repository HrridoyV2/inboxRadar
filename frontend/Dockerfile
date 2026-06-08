FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package.json ./
RUN npm install

# Copy frontend source code
COPY . .

# Expose port
EXPOSE 3000

# Run frontend with dynamic port for Render
CMD ["sh", "-c", "npm run dev -- -p ${PORT:-3000}"]
