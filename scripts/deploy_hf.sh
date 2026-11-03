#!/data/data/com.termux/files/usr/bin/bash
# Deploy the FastAPI backend to a Hugging Face Docker Space. Create the Space first (SDK: Docker, blank).
set -e
HF_USER="${1:?usage: bash scripts/deploy_hf.sh <hf-username> [space-name]}"; SPACE="${2:-orbitsentry-api}"
read -rsp "Hugging Face write token: " TOK; echo
T=$(mktemp -d)
git clone "https://$HF_USER:$TOK@huggingface.co/spaces/$HF_USER/$SPACE" "$T/s"
cp hf-space/README.md "$T/s/README.md"; cp hf-space/Dockerfile "$T/s/Dockerfile"; cp requirements.txt "$T/s/"; cp -r src config "$T/s/"
( cd "$T/s" && git add . && (git commit -m "Deploy OrbitSentry API" || true) && git push )
rm -rf "$T"
echo "Now add Space secrets: API_KEYS, CORS_ORIGINS, GROQ_API_KEY (optional). URL: https://$HF_USER-$SPACE.hf.space"
