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
${SB} copyTo "gitxn_reads_demo.teal"
${SB} copyTo "clear.teal"

# If an .GITXN_APP_ID file exists the ID from there will be used, otherwise it will
# deploy a new application and store the ID in it.
if [ -f ".GITXN_APP_ID"  ]; then
	GITXN_APP_ID=$(cat .GITXN_APP_ID)
else
	GITXN_APP_ID=$(${GOAL} app create --creator ${CREATOR} --approval-prog gitxn_reads_demo.teal --clear-prog clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 | grep 'Created app with app index' | awk '{print $6}' | tr -d '\r')
	echo $GITXN_APP_ID > .GITXN_APP_ID
fi;
APP_ADDR=$(${GOAL} app info --app-id ${GITXN_APP_ID} | grep 'Application account:' | awk '{print $3}' | tr -d '\r')

# If an .INT1_ID file exists the ID from there will be used, otherwise it will
# deploy a new application and store the ID in it.
if [ -f ".INT1_ID" ]; then
	INT1_ID=$(cat .INT1_ID)
else
	INT1_ID=$(${GOAL} app create --creator ${CREATOR} --approval-prog clear.teal --clear-prog clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 | grep 'Created app with app index' | awk '{print $6}' | tr -d '\r')
	echo $INT1_ID > .INT1_ID
fi;

# Application calls

# Have the creator fund the application with a small amount of Algo first.
${GOAL} clerk send -a 1000000 -f ${CREATOR} -t ${APP_ADDR}

# Make an application
${GOAL} app method --app-id ${GITXN_APP_ID} --method "gitxn_demo(account,account,application)void" -f ${USER2} --app-account ${USER2} --app-account ${CREATOR} --foreign-app ${INT1_ID} --arg ${USER2} --arg ${CREATOR} --arg ${INT1_ID} --fee 8000

#${GOAL} app method --app-id ${GITXN_APP_ID} --method "gitxn_demo(account,account,application)void" -f ${USER1} --app-account ${USER2} --app-account ${CREATOR} --foreign-app ${INT1_ID} --arg ${USER2} --arg ${CREATOR} --arg ${INT1_ID} --fee 8000 -o appl_call.txn
#${GOAL} clerk sign -i appl_call.txn -o appl_call.stxn
#${GOAL} clerk dryrun --dryrun-dump -t appl_call.txn -o appl_call.dr
#${SB} copyFrom appl_call.stxn
#${SB} copyFrom appl_call.dr

