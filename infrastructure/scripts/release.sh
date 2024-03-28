#!/bin/bash
# Usage:
## Just pass the name of the env we want to tag and deploy.
## This will create a tag locally with a format of $$ENV-$BRANCH-$CURRENT_USER-$TIMESTAMP
## Then push it to the remote git.
ENV=$1
BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_USER=$(whoami)
TIMESTAMP=$(date +%d-%m-%y--%H%M%S)
TAG_NAME="release-$ENV-$BRANCH-$CURRENT_USER-$TIMESTAMP"

echo "Current branch name is" "$BRANCH"
echo "Current environment name is" "$ENV"
echo "Timestamp assigned will be $TIMESTAMP"
echo "New tag name will be " "$TAG_NAME"

if [ $ENV == 'prod' ]; then
    echo ''
    if [ $BRANCH != 'main' ]; then
        echo -e "\033[0;31mYou can only deploy to prod through a PR into main\033[0m"
        exit 0
    fi
fi

##
echo "Removing Local tags"
git tag -d $(git tag -l)

# Command to run
echo "Applying local tag" && \
git tag "$TAG_NAME" && \
echo "Pushing tag" && \
git push origin $TAG_NAME
