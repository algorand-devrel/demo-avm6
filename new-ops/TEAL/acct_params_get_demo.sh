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
${SB} copyTo "acct_params_get_demo.teal"
${SB} copyTo "clear.teal"

# If an .ACCT_APP_ID file exists the ID from there will be used, otherwise it will
# deploy a new application and store the ID in it.
if [ -f ".ACCT_APP_ID"  ]; then
	ACCT_APP_ID=$(cat .ACCT_APP_ID)
else
	ACCT_APP_ID=$(${GOAL} app create --creator ${CREATOR} --approval-prog acct_params_get_demo.teal --clear-prog clear.teal --global-byteslices 0 --global-ints 0 --local-byteslices 0 --local-ints 0 | grep 'Created app with app index' | awk '{print $6}' | tr -d '\r')
	echo $ACCT_APP_ID > .ACCT_APP_ID
fi;

# Application calls

# Check our local flag (file exists) to see if the account has already opted in
# or if we should opt in now.
if [ ! -f ".ACCT_OPTED_IN" ]; then
	# OptIn to the application. Note that the user MUST have at least 10 Algo
	# after subtracting their minimum balance requirement in order to
	# successfully OptIn.
	${GOAL} app optin --app-id ${ACCT_APP_ID} -f ${USER1}
	touch ".ACCT_OPTED_IN"
fi;

# Perform a NoOp application call as the user to demonstrate the user being
# opted in.
${GOAL} app call --app-id ${ACCT_APP_ID} -f ${USER1}

# Delete the application. This can only be done by the creator account IF they
# haven't rekeyed their account.
${GOAL} app delete --app-id ${ACCT_APP_ID} -f ${CREATOR}
rm ".ACCT_APP_ID"
rm ".ACCT_OPTED_IN"

