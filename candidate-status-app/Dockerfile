# Use the latest Node.js 20 image as the base
FROM node:20

# Set working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application for production
RUN npm run build

# Install a simple HTTP server to serve the build
RUN npm install -g serve

# Expose the port the app runs on
EXPOSE 8080

# Serve the app
CMD ["serve", "-s", "dist"]
