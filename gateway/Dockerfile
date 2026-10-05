FROM nodered/node-red:4.1.15-22

# v1 / v2 - baked into the image, shown on the dashboard and stored in the gateway twin
ARG GATEWAY_VERSION=v1
ENV GATEWAY_VERSION=${GATEWAY_VERSION}

# Node-RED Dashboard (the library monitoring UI at /ui)
RUN npm install --no-audit --no-fund --omit=dev node-red-dashboard@3.6.6

# the gateway flow lives inside the image, so every container starts with the same logic
COPY --chown=node-red:node-red flows.json /usr/src/node-red/flows/flows.json
ENV FLOWS=/usr/src/node-red/flows/flows.json
