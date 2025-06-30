FROM node:18

WORKDIR /app

# Install Quasar CLI
RUN npm install -g @quasar/cli

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

EXPOSE 9000

CMD ["quasar", "dev", "--host", "0.0.0.0", "--port", "9000"]
