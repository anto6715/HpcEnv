#!/bin/bash

otp_token=$(pass cmcc/juno/authenticator)
second_fact=$(oathtool --totp=SHA1 -b "${otp_token}")

echo "${second_fact}" | xclip -selection clipboard
echo "Copied OTP code to clipboard. Will clear in 45 seconds."

(sleep 45 && echo -n | xclip -selection clipboard &)
