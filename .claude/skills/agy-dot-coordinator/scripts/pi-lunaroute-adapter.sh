#!/bin/sh
exec env LUNAROUTE_API_KEY="${LUNAROUTE_API_KEY:-$(lunaroute key)}" "${PI_EXECUTABLE:-pi}" --provider lunaroute --model "${PIL_MODEL:-deepseek-4.1-flash}" "$@"
