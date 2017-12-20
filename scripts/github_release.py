#! /usr/bin/env python
"""
github_release.py - push release assets from CircleCI to GitHub

Uses the GitHub v3 API:
https://developer.github.com/v3/repos/releases/

Add a deployment section to circle.yml in your repo
https://circleci.com/docs/1.0/configuration/#tags

     deployment:
       release:
         tag: /v\d+(\.\d+)*/
         commands:
           - pip install -r scripts/requirements-ci.txt
           - tar zcf scripts.tar.gz scripts
           - ./scripts/github_release.py scripts.tar.gz

Make a personal access token in GitHub:
https://github.com/settings/tokens

Set the token as an environment variable in CircleCI
https://circleci.com/gh/GH_USER/GH_REPO/edit#env-vars

    GH_TOKEN <your_gh_token>

CircleCI will make a new build and push the release assets to GitHub
when you push a tag.

    git commit
    git tag v0.0.1
    git push origin v0.0.1

"""

import requests
import click
import uritemplate
import os
import magic
mime = magic.Magic(mime=True)


def assert_response(r, expect_status, url):
    assert r.status_code == expect_status, \
           "unexpected response=%s expected=%s url=%s text=%s" \
           % (r.status_code, expect_status, url, r.text)


@click.command()
@click.option("--gh_token", "-k", required=True,
              envvar='GH_TOKEN')
@click.option("--gh_tag",   "-t", required=True,
              envvar='CIRCLE_TAG')
@click.option("--gh_user",  "-u", required=True,
              envvar='CIRCLE_PROJECT_USERNAME')
@click.option("--gh_repo",  "-r", required=True,
              envvar='CIRCLE_PROJECT_REPONAME')
@click.argument("filenames", nargs=-1, type=click.Path(exists=True))
def main(gh_token, gh_tag, gh_user, gh_repo, filenames):
    gh_api_root = 'https://api.github.com'
    sess = requests.Session()
    sess.headers.update({'Authorization': 'token %(gh_token)s' % locals(),
                         'Accept': 'application/vnd.github.v3+json'})

    url = ('%(gh_api_root)s'
           '/repos/%(gh_user)s/%(gh_repo)s'
           '/releases') % locals()
    r = sess.post(url, json={
        "tag_name": gh_tag,
        "target_commitish": "master",
        "name": gh_tag,
        "body": gh_tag,
        "draft": False,
        "prerelease": False
        })
    if r.status_code == 422:
        assert False, "tag already exists!  Delete it first to update it."
    assert_response(r, 201, url)
    r = r.json()
    release_id = r['id']
    release_upload_url = r['upload_url']

    try:
        for filename in filenames:
            content_type = mime.from_file(filename)
            with open(filename, 'rb') as f:
                name = os.path.basename(filename)
                url = uritemplate.expand(release_upload_url, name=name)
                r = sess.post(url, files={'file': (name, f, content_type)})
                assert_response(r, 201, url)
                r = r.json()
                print("download_url: %s" % r['browser_download_url'])
    except:
        url = ('%(gh_api_root)s'
               '/repos/%(gh_user)s/%(gh_repo)s'
               '/releases/%(release_id)s') % locals()
        r = sess.delete(url)
        if r.status_code != 204:
            print("WARNING: caught error but couldn't delete release."
                  " response=%s url=%s text=%s"
                  % (r.status_code, url, r.text))
        raise


if __name__ == '__main__':
    main()
