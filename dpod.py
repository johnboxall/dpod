#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import hashlib
import importlib
import itertools
import json
import netrc
import os
import subprocess
import time

import requests

import boto
import boto.s3.key
import boto.s3.lifecycle


###
# GitHub
###

GitHubConfig = collections.namedtuple("GitHubConfig", ["token", "user", "repo", "branch"])

def get_github_config():
    '''
    Returns a configured `GitHubConfig` instance for the working directory.

    '''
    token = os.environ["GITHUB_API_TOKEN"]
    url = subprocess.check_output("git config --get remote.origin.url", shell=True).strip()
    user, repo = parse_github_remote_url(url)
    branch = subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True).strip()
    return GitHubConfig(token, user, repo, branch)

def parse_github_remote_url(uri):
    '''
    Returns a tuple `(username, reponame)` from the git remote `uri`.

    '''
    _, path = uri.split(":", 1)
    user, repo = path.split("/", 1)
    repo, _ = repo.rsplit(".", 1)
    return user, repo

def get_tarball_from_github(config):
    '''
    Returns an application tarball using the Contents API:

        https://developer.github.com/v3/repos/contents/#get-archive-link

    '''
    url = "https://api.github.com/repos/%s/%s/tarball/%s" % (config.user, config.repo, config.branch)
    session = requests.Session()
    session.auth = ('token', config.token)
    response = session.get(url)
    response.raise_for_status()
    return response.content


###
# S3
###

S3Config = collections.namedtuple("S3Config", ["connection", "bucket", "key"])

def get_s3_config():
    '''
    Returns an `S3Config` instance from the current environment variable settings.

    '''
    connection = boto.connect_s3()
    bucket = "dpod-%s" % connection.gs_access_key_id.lower()
    key = "app.tgz"
    return S3Config(connection, bucket, key)

def setup_s3(config):
    '''
    Creates an S3 bucket configured to automatically expire files.

    '''
    try:
        bucket = config.connection.create_bucket(config.bucket)
    except boto.exception.S3CreateError as err:
        print err
        return

    lifecycle = boto.s3.lifecycle.Lifecycle()
    lifecycle.add_rule(id="expire keys after one day",
                       prefix="",
                       status="Enabled",
                       expiration=boto.s3.lifecycle.Expiration(days=1))

    bucket.configure_lifecycle(lifecycle)

def upload_to_s3(config, content):
    '''
    Uploads the string `content` to S3.

    '''
    bucket = config.connection.get_bucket(config.bucket, validate=False)
    key = boto.s3.key.Key(bucket)
    key.key = config.key
    key.set_contents_from_string(content)
    return key


###
# Heroku
###

HerokuConfig = collections.namedtuple("HerokuConfig", ["token"])

def get_heroku_config():
    '''
    Returns a `HerokuConfig` instance configured from `~/.netrc` settings.

    '''
    hosts = netrc.netrc().hosts
    _, _, token = hosts["api.heroku.com"]
    return HerokuConfig(token)

def create_heroku_app(config, source_url):
    '''
    Returns a tuple `(app_name, app_setup_id)` for an app created with the
    Heroku App Setup Create API:

        https://devcenter.heroku.com/articles/platform-api-reference#app-setup-create

    '''
    url = "https://api.heroku.com/app-setups"
    headers = {"Accept": "application/vnd.heroku+json; version=3"}
    data = {"source_blob": {"url": source_url}}
    session = requests.Session()
    session.auth = ("", config.token)
    response = session.post(url, data=json.dumps(data), headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["app"]["name"], data["id"]

def check_heroku_app_status(config, app_setup_id):
    '''
    Checks the status of an app using the Heroku App Setup Info API:

        https://devcenter.heroku.com/articles/platform-api-reference#app-setup-info

    '''
    url = "https://api.heroku.com/app-setups/%s" % app_setup_id
    headers = {"Accept": "application/vnd.heroku+json; version=3"}
    session = requests.Session()
    session.auth = ("", config.token)
    response = session.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    succeeded = data["status"] == "succeeded"
    return succeeded


###
# CLI
###

def cli():
    github_config = get_github_config()
    s3_config = get_s3_config()
    heroku_config = get_heroku_config()

    setup_s3(s3_config)

    tarball = get_tarball_from_github(github_config)
    tarball_key = upload_to_s3(s3_config, tarball)
    signed_tarball_url = tarball_key.generate_url(expires_in=60)

    app_name, app_setup_id = create_heroku_app(heroku_config, signed_tarball_url)

    while True:
        time.sleep(5)
        succeeded = check_heroku_app_status(heroku_config, app_setup_id)
        if succeeded:
            break

    print 'http://%s.herokuapp.com' % app_name


if __name__ == "__main__":
    cli()