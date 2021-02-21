#! /bin/sh

apk --no-cache add curl chromium  alpine-sdk

pip install --no-cache-dir -r requirements.txt

export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

python -c "import nltk; nltk.download('punkt')"