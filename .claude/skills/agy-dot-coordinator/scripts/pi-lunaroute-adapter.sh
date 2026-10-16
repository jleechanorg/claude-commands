#!/bin/sh
exec env LUNAROUTE_API_KEY="$(lunaroute key)" pi --provider lunaroute --model deepseek-4.1-flash "$@"
