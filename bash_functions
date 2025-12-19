#!/bin/bash

function 2fa_juno() {
    local otp_token; otp_token=$(pass cmcc/juno/authenticator)
    local second_fact; second_fact=$(oathtool --totp=SHA1 -b "${otp_token}")

    echo "${second_fact}" | xclip -selection clipboard
    echo "Copied OTP code to clipboard. Will clear in 45 seconds."

    (sleep 45 && echo -n | xclip -selection clipboard &)

}
export -f 2fa_juno

bjobs_stats() {
    local user="${1:-"$(whoami)"}"
    bjobs -a -o "jobid stat job_name run_time start_time finish_time exec_host" -u "${user}" |sort
}
export -f bjobs_stats
