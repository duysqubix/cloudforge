#!/bin/sh 

if [ "${1#-}" != "${1}" ] || [ -z "$(command -v "${1}")" ]; then
  set -- cli "$@"
fi

exec "$@"