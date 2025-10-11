#!/bin/bash
set -e
. $(dirname $0)/.utils.sh

CONTEXT=persistence run $(dirname $0)/persistence/install-dependancies.sh
CONTEXT=persistence run $(dirname $0)/persistence/daily-live-backup.sh
CONTEXT=persistence run $(dirname $0)/persistence/distribute-latest-daily.sh