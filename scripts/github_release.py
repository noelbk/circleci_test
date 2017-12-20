#! /usr/bin/env python
"""
github_release.py - upload files to a tagin a circleci build
"""
# https://circleci.com/docs/1.0/configuration/#tags
#
# deployment:
#   release:
#     tag: /v[0-9]+(\.[0-9]+)*/
#     commands:
#       - npm pack
#       - ./github_release.py vis-$VERSION.tar.gz
#
# https://circleci.com/docs/1.0/environment-variables/

import requests
import click

@click.command()
@click.option("--gh_tag",   "-t", envvar='CIRCLE_TAG', required=True)
@click.option("--gh_user",  "-u", envvar='CIRCLE_PROJECT_USERNAME', required=True)
@click.option("--gh_repo",  "-r", envvar='CIRCLE_PROJECT_REPONAME', required=True)
@click.option("--gh_token", "-k", envvar='GH_TOKEN', required=True)
@click.argument("filenames", nargs=-1, type=click.Path(exists=True))
def main(gh_tag, gh_user, gh_repo, gh_token, filenames):
    print(
        " gh_tag=%(gh_tag)s"
        " gh_user=%(gh_user)s"
        " gh_repo=%(gh_repo)s"
        " gh_token=%(gh_token)s"
        " filenames=%(filenames)s"
        % locals())
    return    
    
    s = requests.Session()
    s.headers.update({'Authorization': 'token %(gh_token)s' % locals()})

    url = 'https://api.github.com/repos/%(gh_owner)s/$(gh_repo)s/releases/tags/%(gh_tag)s' % locals()
    br = s.get(url)
    assert r.status_code == 404, "tag already exists"
    
    url = 'https://api.github.com/repos/%(gh_owner)s/%(gh_repo)s/releases' % locals()
    r = s.post(url, data={
      "tag_name": gh_tag,
      "target_commitish": "master",
      "name": gh_tag,
      "body": gh_tag,
      "draft": false,
      "prerelease": false
    })
    assert r.status_code == requests.codes.ok
    r = r.json()
    release_id = r['id']
    release_upload_url = r['upload_url']

    for filename in filenames:
        with open(filename, 'rb') as f:
            url = 'https://%(release_upload_url)s/repos/%(gh_owner)s/%(gh_repo)/releases/%(release_id)s/assets?name=%(filename)s' % locals()
            r = requests.post(url, data=f)
            assert r.status_code == requests.codes.ok

if __name__ == '__main__':
    main()
    
