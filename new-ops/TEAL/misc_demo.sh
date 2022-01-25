#!/usr/bin/env bash

set -euxo pipefail

# You may need to change the SB variable to the location of your sandbox 
# installation.
SB="$HOME/sandbox/sandbox"
GOAL="${SB} goal"

# Fetch the default accounts from sandbox.
# The first account will be considered the "creator" who deploys all contracts.
# The second and third accounts will be users of the contracts.
ACCOUNTS=($(${GOAL} account list | awk '{print $3}'))
CREATOR=${ACCOUNTS[0]}
USER1=${ACCOUNTS[1]}
USER2=${ACCOUNTS[2]}

# Copy the approval and clearstate TEAL files to the sandbox.
${SB} copyTo "misc_demo.teal"
${SB} copyTo "clear.teal"

# If an .INT1_ID file exists the ID from there will be used, otherwise it will
# deploy a new application and store the ID in it.
if [ -f ".INT1_ID" ]; then
	INT1_ID=$(cat .INT1_ID)
else
	INT1_ID=$(${GOAL} app create --creator ${CREATOR} --approval-prog clear.teal --clear-prog clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 | grep 'Created app with app index' | awk '{print $6}' | tr -d '\r')
	echo $INT1_ID > .INT1_ID
fi;

# If an .MISC_APP_ID file exists the ID from there will be used, otherwise it will
# deploy a new application and store the ID in it.
if [ -f ".MISC_APP_ID"  ]; then
	MISC_APP_ID=$(cat .MISC_APP_ID)
else
	MISC_APP_ID=$(${GOAL} app create --creator ${CREATOR} --approval-prog misc_demo.teal --clear-prog clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 | grep 'Created app with app index' | awk '{print $6}' | tr -d '\r')
	echo $MISC_APP_ID > .MISC_APP_ID
fi;

# Application calls

# Call the method "opcode_budget_demo()uint64" and the return value will be the
# opcode budget by the end of the script.
${GOAL} app method --app-id ${MISC_APP_ID} --method "opcode_budget_demo()uint64" -f ${USER1} --fee 2000 --foreign-app ${INT1_ID}

# Call the method "bsqrt_demo(byte[])byte" with a byte-array and the return
# value will be the result after evaluating it with the opcode `bsqrt`.
${GOAL} app method --app-id ${MISC_APP_ID} --method "bsqrt_demo(byte[])byte" -f ${USER1} --arg '[128]'

