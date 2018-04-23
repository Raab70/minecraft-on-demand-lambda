# minecraft-on-demand-lambda

Turnkey solution for on-demand pushbutton minecraft server

Forked from [d10n/minecraft-on-demand-lambda](https://github.com/d10n/minecraft-on-demand-lambda)
Changes:
* destroy and deploy no longer run terraform from a lambda which is clunky. They
use the boto3 APIs to simply stop the server instance. This has the advantage
of being simpler and more reliable (I had issues with running terraform w/in
lambda). However it does cost slightly more as the EBS volume is not destroyed.
* Because of the first change the status is now read directly from the instance
status instead of inferred from terraform.
* Discord now optional. The discord send message would not work for me
so it will now work even if discord bot integration fails.

## Features

 * Creates an API URL that deploys the server
 * Auto shutoff after 30 minutes
 * Backup every 5 minutes
 * Costs about $0.30/mo with light usage. (From d10n, not confirmed)

## Instructions

Requirements:

 * Terraform
 * JDK 1.8 (if you want spigot)
 * An ssh key pair to SSH into the running Minecraft server:

       ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_minecraft

 * Ensure you have awscli credentials configured: <http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>
 * Copy core/terraform.tfvars.example to core/terraform.tfvars and fill in the values.
    * See the variables section below for instructions to get the values.
    * The s3 buckets and dynamodb tables will be created with the supplied names; you don't need to create them manually
 * Edit the backend variables at the top of instance/instance.tf

### Initial setup

1. Copy `core/terraform.tfvars.example` to `core/terraform.tfvars`
1. Fill in `core/terraform.tfvars`, for more help see the [Variables](#Variables) section.
1. `make` will build the lambdas and deploy everything, also creating your minecraft server instance immediately.
1. Spigot setup (optional): `make spigot` # if you prefer spigot to vanilla minecraft

## Variables

To get the discord client token:
 * Click "New Application" on the Applications page: <https://discordapp.com/developers/applications/me>
 * Enter a name and click "Create Application"
 * Click "Create Bot User" and click the confirmation button
 * Click the token reveal link

To add the discord bot to your channel (and get the channel ID):
 * Get the Client ID from the top of your bot's page
 * Visit <https://discordapp.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot&permissions=2048>
 * Follow the instructions to add the bot to your channel
 * On Discord, open User Settings -> Appearance -> Enable Developer Mode
 * Right click on the channel that you added the bot to and click "Copy ID" to get the channel ID

To get the AWS access key and secret key:
 * Visit the IAM console and click Add User
 * Set a user name, check Programmatic Access, and click Next
 * Click the Create group button, enter a group name, check AdministratorAccess, and click Create Group
 * Click Next and then click Create user
 * Write down the Access key ID and Secret access key from the success page, because this is the last time you can get the secret access key!

To get the region:
 * Pick one from the Region column in the tables at <https://docs.aws.amazon.com/general/latest/gr/rande.html>. Make sure it supports Amazon API Gateway and AWS Lambda.
 * I suggest us-east-1

The SSH terraform public key should point to the public key you want to use to SSH into the Minecraft server.

For dynamodb and s3 names, any value is fine as long as it hasn't been used by another AWS user.


## Repository layout

 * `core` configures the AWS infrastructure that can create the Minecraft server on demand
 * `core/core.tf` configures all of the permanent AWS resources, like the S3 buckets, Lambda functions, and API Gateway methods
 * `core/terraform.tfvars` holds your individual settings
 * `core/variables.tf` tells terraform what variables to expect
 * `core/auto_shutoff.py` is downloaded by the instance and periodically run to shut the server off if there were no players for the last 30 minutes
 * `core/lambda_destroy_deploy/lambda_destroy_deploy.py` is the code for the Lambda destroy and deploy functions
 * `core/lambda_status/lambda_status.py` is the code for the Lambda status function
 * `core/lambda_status/requirements.txt` lists the dependencies to be installed for `lambda_status.py`
 * `core/instance.tf` configures all of the on-demand AWS resources, including the Minecraft EC2 server and its VPC

 * `web/index_src.html` is the template for `web/index.html`. The core deployment plugs in the deploy and status URLs.
 * `web/index.html` is a basic web page with a button to deploy the Minecraft server

 * `Makefile` has recipes to run all the required setup commands in the right order
    * `make` deploys or updates the core
    * `make init` initializes your terraform backend
    * `make plan` runs `terraform plan` after building the lambda function zip file
    * `make info` shows the variable output from the core deployment
    * `make spigot` compiles spigot and uploads it to your s3 world bucket
    * `make terraform-bundle` compiles a terraform bundle with all provider dependencies included (not currently used)


## Notes

 * If you need more RAM, set a bigger instance size than t2.micro in instance.tf and increase Xmx and Xms in `provision_minecraft.sh` to be a little below the instance size's total allocated RAM
 * The Lambda functions can have bundled dependencies or they can install dependencies when they run. I don't know which I prefer yet and I have both approaches: the destroy and deploy functions install dependencies at runtime, while the status function bundles its dependencies.
 * Elastic IP is a static IP that works across redeploys of the server. Using Elastic IP is convenient to avoid DNS TTL caching, but it costs extra. Enable by uncommenting all blocks containing "eip" references in `core/core.tf` and `core/instance.tf`.
 * Restore from backups using [s3-pit-restore](https://github.com/madisoft/s3-pit-restore)
    * Example:
      ```
      s3-pit-restore --bucket d10n-minecraft-world-backup --dest world-restore --timestamp '2017-10-11 4:30PM EDT'
      aws s3 sync --delete world-restore s3://d10n-minecraft-world-backup
      ```

## TODO
Improvements and ideas
* Fix discord integration, add discord commands to start/stop the server.
This is challenging since discord bots, unlike slack bots, cannot be set to
hit a webhook and must be listening (of polling). Meaning lambda discord bots
are not a simple idea and paying to run a nano instance for the discord bot
nearly defeats the purpose of all the work to make this as cost effective
as possible. This would be relatively simple with an existing discord bot however.
* Destroy EBS volume. Then you would need to restore a new one from a snapshot
at deployment. Seems like a lot of hassle for such a small EBS volume.
* Restore API endpoint would be a nice addition
* Route53 alias of s3 bucket for easier access?

