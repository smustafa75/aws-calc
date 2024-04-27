The purpose of repo is to extract and showcase pricing api results.
Work in progress.

https://stackoverflow.com/questions/51673667/use-boto3-to-get-current-price-for-given-ec2-instance-type

https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-list-bulk-api-step-2-find-available-price-list-files.html

https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html

fetch_prices01.py is a refernce code taken from stackoverflow.

git filter-branch --env-filter 'if [ "$GIT_AUTHOR_EMAIL" = "sabir.mustafa@citrusconsulting.com" ]; then
     GIT_AUTHOR_EMAIL=sabir1p2p@gmail.com;
     GIT_AUTHOR_NAME="Sabir Mustafa";
     GIT_COMMITTER_EMAIL=$GIT_AUTHOR_EMAIL;
     GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"; fi' -- --all