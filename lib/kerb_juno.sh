#!/bin/bash


##
## Author Antonio Mariani (antonio.mariani@cmcc.it)
##
## Generate the password needed to connect to Juno, then start kerberos to obtain the 24 certificate.
## When kerberos prompt appears, it's  sufficient to press ctrl+v because the password is stored automatically in the clipboard.
## Clean the clipboard when the execution ends
##


juno_usr=$(pass cmcc/juno/user)
juno_pwd=$(pass cmcc/juno/password)
otp_token=$(pass cmcc/juno/authenticator)

second_fact=$(oathtool --totp=SHA1 -b "${otp_token}")
echo "${juno_pwd}${second_fact}" | xclip -selection clipboard

# Notify the user
echo "String copied to clipboard. Press ctrl+v to copy the password"

kinit -n
kinit -T "FILE:/tmp/krb5cc_$(id -u)" "${juno_usr}"

# Clear the clipboard by copying an empty string
echo -n | xclip -selection clipboard

# Notify the user
echo "Clipboard cleared."
