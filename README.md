    ________                     __________          .___
    \______ \_______  ____ ______\______   \____   __| _/
     |    |  \_  __ \/  _ \\____ \|     ___/  _ \ / __ |
     |    `   \  | \(  <_> )  |_> >    |  (  <_> ) /_/ |
    /_______  /__|   \____/|   __/|____|   \____/\____ |
            \/             |__|                       \/

# DropPod

DropPod is a CLI for deploying a private GitHub repository to Heroku.

DropPod uses the [GitHub Contents API](https://developer.github.com/v3/repos/contents/#get-archive-link)
to retrieve the application tarball. The tarball is pushed to S3 and a signed URL
is then passed to the [Heroku App Setup API](https://devcenter.heroku.com/articles/platform-api-reference#app-setup-create)
to launch a new instance of the app.

## Install

The development version of DropPod can be installed from GitHub:

    pip install --upgrade https://github.com/johnboxall/dpod/tarball/master

### Setup

DropPod requires permissions to GitHub, S3 and Heroku.

* GitHub:   Requires `repo` scope to the private repository.
            [Create a `repo` access token](https://github.com/settings/tokens/new)
            and store it in the environment variable `GITHUB_API_TOKEN`. The repo
            must include a valid [app.json](https://blog.heroku.com/archives/2014/5/22/introducing_the_app_json_application_manifest).
* S3 (AWS): Requires write access to an S3 bucket to temporarily store
            the app tarball. It is not currently possible to pass
            the result of the GitHub Content API call directly to Heroku.
            Uses the environment variables `AWS_ACCESS_KEY_ID` and
            `AWS_SECRET_ACCESS_KEY`. The default bucket name is
            `dpod-$AWS_ACCESS_KEY_ID`.
* Heroku:   Requires a Heroku key to launch the app. Uses the key found in
            the api.heroku.com entry from `~/.netrc`.

## Usage

From within a git repo with a GitHub remote `origin` run:

    $ dpod

DropPod deploys the latest version of the checked out branch that is available
on GitHub to Heroku.

## Todo

* [ ] Allow configuration from the command line
* [ ] Support streaming uploads
* [ ] Bug GitHub to increase Contents API expiry time to remove AWS requirement
* [ ] Error handling
* [ ] Progress logging
* [ ] Output formatting eg. JSON