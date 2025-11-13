#!/bin/bash

action=$1
service=$2
command=$3

if [ "$action" == "build" ]; then
    docker-compose up --build -d
elif [ "$action" == "up" ]; then
    docker-compose up -d
elif [ "$action" == "down" ]; then
    docker-compose down
elif [ "$action" == "shell" ]; then
    docker-compose exec app bash -c "python app/shell.py"
elif [ "$action" == "exec" ]; then
    if [ -z "$service" ] || [ -z "$command" ]; then
        echo "Usage: $0 exec <service> <command>"
        exit 1
    fi
    docker-compose exec "$service" "$command"
elif [ "$action" == "logs" ]; then
    if [ -z "$service" ]; then
        echo "Usage: $0 logs <service>"
        exit 1
    fi
    docker-compose logs -f --tail 100 "$service"
else
    echo "Invalid action: $action"
    echo "Usage: $0 <build|up|down|exec|logs> [service] [command]"
    exit 1
fi
