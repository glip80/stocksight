#! /bin/sh

apk --no-cache add curl chromium  alpine-sdk postgresql-dev

pip install --no-cache-dir -r requirements.txt

export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

nltk_packages=$(cat nltk.txt |tr "\n" " ")
python -m nltk.downloader $nltk_packages
# python -c "import nltk; nltk.download('punkt')"