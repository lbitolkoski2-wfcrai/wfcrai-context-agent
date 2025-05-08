# syntax = docker/dockerfile:1.2
FROM python:3.13-slim

# install curl, gcloud creds helper & certs
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates

 ADD https://astral.sh/uv/install.sh /uv-installer.sh
 RUN sh /uv-installer.sh && rm /uv-installer.sh \
  && pip install keyrings.google-artifactregistry-auth google-auth
 
 ENV PATH="/root/.local/bin/:$PATH" \
     UV_KEYRING_PROVIDER=subprocess \
     UV_INDEX_PRIVATE_REGISTRY_USERNAME=oauth2accesstoken \
     GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/adc
 
 # copy your app & lockfile
 COPY . /app
 WORKDIR /app
 
 # install your private package from GAR via UV
 # mount only the ADC JSON so keyrings.google-artifactregistry-auth can find it
 RUN --mount=type=secret,id=adc \
     uv add wfcrai-agent-utils \
       --keyring-provider subprocess \
       --index https://oauth2accesstoken@us-central1-python.pkg.dev/gcp-wow-food-wfc-ai-dev/wfcrai-agent-utils/simple/
 
 # install the rest of your deps
 RUN uv sync --frozen
 
 EXPOSE 8000
 ENTRYPOINT ["uv","run","uvicorn","main:app","--host","0.0.0.0","--port","8000"]
 CMD []