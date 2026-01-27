#!/bin/sh

echo "==== entrypoint debug ===="

if [ -z "$GOOGLE_API_KEY" ]; then
  echo "GOOGLE_API_KEY: NOT SET"
else
  # mask all but first/last 4 chars if long enough
  if [ ${#GOOGLE_API_KEY} -gt 8 ]; then
    prefix=$(printf "%s" "$GOOGLE_API_KEY" | cut -c1-4)
    suffix=$(printf "%s" "$GOOGLE_API_KEY" | rev | cut -c1-4 | rev)
    echo "GOOGLE_API_KEY: set (masked) ${prefix}...${suffix}"
  else
    echo "GOOGLE_API_KEY: set (short)"
  fi
fi

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
  echo "GOOGLE_MAPS_API_KEY: NOT SET"
else
  if [ ${#GOOGLE_MAPS_API_KEY} -gt 8 ]; then
    prefix=$(printf "%s" "$GOOGLE_MAPS_API_KEY" | cut -c1-4)
    suffix=$(printf "%s" "$GOOGLE_MAPS_API_KEY" | rev | cut -c1-4 | rev)
    echo "GOOGLE_MAPS_API_KEY: set (masked) ${prefix}...${suffix}"
  else
    echo "GOOGLE_MAPS_API_KEY: set (short)"
  fi
fi

echo "Files in /app (top 50):"
ls -la /app | sed -n '1,50p'

echo "Running: $@"

# Execute the original CMD
exec "$@"
