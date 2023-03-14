#!/usr/bin/env bash

BASEDIR="$(dirname "$0")"
COMMIT="$(git rev-parse --short HEAD)"

if [[ -z "$TAG" ]]; then
  echo "Is missing the TAG to deploy" >/dev/stderr
  exit 1
fi

mkdir -p "${BASEDIR}/rendered/values"

echo "templates: " >"${BASEDIR}"/rendered/values/namesetup.yaml
echo "  project: &project" >>"${BASEDIR}"/rendered/values/namesetup.yaml
echo "    name: $PROJECT" >>"${BASEDIR}"/rendered/values/namesetup.yaml
echo "version: \"$TAG\"" >"${BASEDIR}"/rendered/values/version.yaml
echo "commit: \"$COMMIT\"" >>"${BASEDIR}"/rendered/values/version.yaml

cp "${BASEDIR}/helmfile.yaml" "${BASEDIR}/rendered/"
cp "${BASEDIR}/values/base.yaml.gotmpl" "${BASEDIR}/rendered/values/"
cp "${BASEDIR}/values/base-api.yaml.gotmpl" "${BASEDIR}/rendered/values/"
cp "${BASEDIR}/values/${TRIGGER_KIND}.yaml" "${BASEDIR}/rendered/values/"