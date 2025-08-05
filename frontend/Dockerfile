FROM node:24-alpine

WORKDIR /app

# Copy package files and source code
COPY package*.json ./
COPY . .

# Install dependencies
RUN npm install

# Expose port
EXPOSE 9000

# Start development server
CMD ["npm", "run", "dev"]
