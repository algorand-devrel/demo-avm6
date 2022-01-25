#!/usr/bin/env bash

set -euxo pipefail

SB="$HOME/Software/sandbox/sandbox"
GOAL="${SB} goal"

ACCOUNTS=($(${GOAL} account list | awk '{print $3}'))
CREATOR=${ACCOUNTS[0]}
USER1=${ACCOUNTS[1]}
USER2=${ACCOUNTS[2]}

${SB} copyTo misc_demo.teal
${SB} copyTo clear.teal

INT1_ID=$(${GOAL} app create --creator ${CREATOR} --approval-prog clear.teal --clear-prog clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 | grep 'Created app with app index' | awk '{print $6}' | tr -d '\r')
echo $INT1_ID > .INT1_ID

APP_ID=$(${GOAL} app create --creator ${CREATOR} --approval-prog misc_demo.teal --clear-prog clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 | grep 'Created app with app index' | awk '{print $6}' | tr -d '\r')
echo $APP_ID > .APP_ID

${GOAL} app method --app-id ${APP_ID} --method "opcode_budget_demo()uint64" -f ${USER1} --fee 2000 --foreign-app ${INT1_ID}

${GOAL} app method --app-id ${APP_ID} --method "bsqrt_demo(byte[])byte" -f ${USER1} --arg '[128]'

