echo "Building and Pushing Docker image to GCR"
docker build . -t sh-battle:latest
docker tag sh-battle gcr.io/deeprole/sh-battle
docker push gcr.io/deeprole/sh-battle