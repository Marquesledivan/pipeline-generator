# pipeline-generator

This is a Python CLI that generates *.gitlab-ci.yml* output  in **infrastructure-live** repositories.

## Prerequisites

* Python 3.10 or higher
* pip
* docker(optional)

## Install package 

You can make a virtual environment:

```shell
$ python3 -m venv venv
$ source venv/bin/activate
```

Install the package with pip:

```shell
$ pip install .
```

To install in editable mode("develop mode"):
```shell
$ pip install -e .
```


## Executing the CLI

After creating the virtualenv and installing the package you can run the CLI with the following commands located in the root of the infra-live repository:

```shell
$ pipeline-generator
```
The default image for ci/cd pipeline is `"craftech/ci-tools:iac-tools-85d40e6"` and 
the default provider is `gitlab` (generates a .gitlab-ci.yml output style).

To set a custom image use the `-i` flag:
```shell
$ pipeline-generator -i mycustomimage:v1.0.0
```

By default, the branch name is **master**. You can change it with e `-b` or `--branch` option, e.g:

```shell
$ pipeline-generator -b main
```

If you need add a host to ~/.ssh/known_hosts file, use the `-e` option:
```shell
$ pipeline-generator  -e gitlab.foo.com
```

The --extra-know-host option can be passed multiple times:
```shell
$ pipeline-generator  -e gitlab.foo.com -e gitlab.bar.com
```

Instead of printing the result to the screen, you can save it to a file with de `-o` or `--out` option:
```shell
$ pipeline-generator  -e gitlab.foo.com -e gitlab.bar.com -o .gitlab-ci.yml
```

### Download environment variables from Vault

#### Requirements

Image requirements(already installed in the default image):
* jq
* pyhcl

## Examples

```yaml
stages:
  - terragrunt-plan
  - terragrunt-apply

default:
  image: craftech/ci-tools:iac-tools-85d40e6

variables:
  TERRAPLAN_NAME: tfplan

.terragrunt_template: &terragrunt_template
  - mkdir -p ~/.ssh
  - echo "$GITLAB_DEPLOY_KEY" | tr -d '\r' > ~/.ssh/id_rsa
  - chmod 600 ~/.ssh/id_rsa
  - eval $(ssh-agent -s)
  - ssh-add ~/.ssh/id_rsa
  - ssh-keyscan -H git.in.example.com >> ~/.ssh/known_hosts
  - ssh-keyscan -H github.com >> ~/.ssh/known_hosts
  - LOCATION=$(echo ${CI_JOB_NAME} | cut -d":" -f2)
  - cd ${LOCATION}
  - apt update && apt-get install gnupg -y
  - git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.10.2
  - . $HOME/.asdf/asdf.sh
  - asdf plugin-add terraform https://github.com/asdf-community/asdf-hashicorp.git
  - asdf plugin-add terragrunt https://github.com/ohmer/asdf-terragrunt.git
  - asdf install

.aws_cli_terragrunt_template:
  before_script:
    - *terragrunt_template
    - apt-get install awscli -y
    - KST=(`aws sts assume-role --role-arn ${ASSUME_ROLE} --role-session-name "deployment-${CI_PROJECT_NAME}" --query '[Credentials.AccessKeyId,Credentials.SecretAccessKey,Credentials.SessionToken]' --output text`)
    - export AWS_ACCESS_KEY_ID=${KST[0]}
    - export AWS_SECRET_ACCESS_KEY=${KST[1]}
    - export AWS_SESSION_TOKEN=${KST[2]}
    - export AWS_SECURITY_TOKEN=${KST[2]}

.example_terragrunt_plan_template:
  stage: terragrunt-plan
  variables:
    AWS_DEFAULT_REGION: ${AWS_REGION}
    ASSUME_ROLE: arn:aws:iam::000000000000000:role/example-devops-runner
  extends: .aws_cli_terragrunt_template
  tags:
    - example-mgt
  script:
    - terragrunt plan --terragrunt-non-interactive -input=false -refresh=true -out=$TERRAPLAN_NAME

.example_terragrunt_apply_template:
  stage: terragrunt-apply
  variables:
    AWS_DEFAULT_REGION: ${AWS_REGION}
    ASSUME_ROLE: arn:aws:iam::000000000000000:role/example-devops-runner
  extends: .aws_cli_terragrunt_template
  tags:
    - example-mgt
  when: manual
  script:
    - terragrunt apply -input=false -refresh=false -auto-approve=true $TERRAPLAN_NAME

.exemplo_terragrunt_plan_template:
  stage: terragrunt-plan
  before_script:
    - *terragrunt_template
  tags:
    - example-prd
  script:
    - terragrunt plan --terragrunt-non-interactive -input=false -refresh=true -out=$TERRAPLAN_NAME

.exemplo_terragrunt_apply_template:
  stage: terragrunt-apply
  before_script:
    - *terragrunt_template
  tags:
    - example-prd
  when: manual
  script:
    - terragrunt apply -input=false -refresh=false -auto-approve=true $TERRAPLAN_NAME

terragrunt-plan:aws/example/us-east-1/alb/example:
  extends: .example_terragrunt_plan_template
  variables:
    AWS_REGION: us-east-1
  only:
    refs:
      - main
    changes:
      - aws/example/us-east-1/alb/example/*
  artifacts:
    paths:
      - aws/example/us-east-1/alb/example/.terragrunt-cache
    expose_as: 'tfplan'
    expire_in: 1 day

terragrunt-apply:aws/example/us-east-1/alb/example:
  extends: .example_terragrunt_apply_template
  variables:
     AWS_REGION: us-east-1
  only:
    refs:
      - main
    changes:
      - aws/example/us-east-1/alb/example/*
  dependencies:
    - terragrunt-plan:aws/example/us-east-1/alb/example

terragrunt-plan:aws/exemplo/us-east-1/s3/cloudformation-stacksets:
  extends: .exemplo_terragrunt_plan_template
  variables:
    AWS_REGION: us-east-1
  only:
    refs:
      - main
    changes:
      - aws/exemplo/us-east-1/s3/cloudformation-stacksets/*
  artifacts:
    paths:
      - aws/exemplo/us-east-1/s3/cloudformation-stacksets/.terragrunt-cache
    expose_as: 'tfplan'
    expire_in: 1 day

terragrunt-apply:aws/exemplo/us-east-1/s3/cloudformation-stacksets:
  extends: .exemplo_terragrunt_apply_template
  variables:
     AWS_REGION: us-east-1
  only:
    refs:
      - main
    changes:
      - aws/exemplo/us-east-1/s3/cloudformation-stacksets/*
  dependencies:
    - terragrunt-plan:aws/exemplo/us-east-1/s3/cloudformation-stacksets
```

### CLI help

``` shell
$ pipeline-generator --help
Usage: pipeline-generator [OPTIONS]

Options:
  --version                       Show the version and exit.
  -i, --image-registry TEXT       Registry for default image
  -p, --provider [gitlab]         Git provider, i.e: gitlab  [default: gitlab]
  -o, --out TEXT                  Output file name
  -e, --extra-know-host TEXT      Host that will be added to
                                  ~/.ssh/known_hosts. i.e: gitlab.com
  -b, --branch TEXT               Default branch name  [default: master]
  --export-aws-vars               Export AWS variables in the script section
  --help                          Show this message and exit.
```

## Executing with Docker

To build the docker image run the following command in the root of the repository:

```shell
$ docker build -t pipeline-generator:latest .
```

Or use the Docker Hub image(https://hub.docker.com/r/craftech/pipeline-generator/tags)
```shell
docker pull craftech/pipeline-generator:latest
```

Run a temporary container to execute de CLI:

```shell
$ docker run --rm -it --name pipeline-generator --env LOCAL_USER_ID=$(id -u) -v `pwd`:`pwd` -w `pwd` pipeline-generator:latest /bin/sh
```