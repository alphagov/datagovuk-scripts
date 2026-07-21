#!/bin/bash

set -eux

if [[ ${IS_TAG:-} = "true" ]]; then
  export IMAGE_TAG="${GH_REF}"
  export SOURCE_BRANCH="main"
else
  export IMAGE_TAG=$(gh api repos/alphagov/check-links/branches/${GH_REF} | jq .commit.sha -r)
  export SOURCE_BRANCH=${GH_REF}
fi

git config --global user.email "datagovuk-ci@users.noreply.github.com"
git config --global user.name "datagovuk-ci"

gh auth setup-git
git clone https://github.com/alphagov/govuk-dgu-charts.git charts

cd charts/charts/ckan/images

HAS_CHANGED=0
for ENV in $(echo $ENVS | tr "," " "); do
  (
    cd "${ENV}"
    for SUFFIX in '', '-ckan'; do
      (
        yq -i '.tag = env(IMAGE_TAG)' "check-links${SUFFIX}.yaml"
        yq -i '.branch = env(SOURCE_BRANCH)' "check-links${SUFFIX}.yaml"
        git add "check-links${SUFFIX}.yaml"

        if git diff --cached --quiet -- "check-links${SUFFIX} .yaml"; then
          echo "Nothing to commit for check-links${SUFFIX}.yaml in ${ENV}"
        else
          HAS_CHANGED=1
        fi
      )
    done

    if [[ $HAS_CHANGED -eq 1 ]]; then
      BRANCH="ci/${IMAGE_TAG}-${ENV}"
      # Check remote (not local) — git show-ref only sees local refs in a fresh clone
      if git ls-remote --exit-code --heads origin "${BRANCH}" >/dev/null 2>&1; then
        echo "Branch ${BRANCH} already exists on govuk-dgu-charts — skipping"
      else
        git fetch --quiet origin main
        git checkout -b "${BRANCH}" origin/main
        git commit -m "Update check-links image tags for ${ENV} to ${IMAGE_TAG}"
        git push --set-upstream origin "${BRANCH}"
        # gh pr create --title "Update check-links image tags for ${ENV} (${IMAGE_TAG})" --base main --head "${BRANCH}" --fill --repo alphagov/govuk-dgu-charts
      fi
    fi
  )
done
